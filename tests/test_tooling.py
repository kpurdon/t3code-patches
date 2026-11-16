import contextlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import plistlib
import struct
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('patch_tool', str(ROOT / 't3code-patches'))
spec = importlib.util.spec_from_loader(loader.name, loader)
tool = importlib.util.module_from_spec(spec)
loader.exec_module(tool)


def asar(path, files):
    tree = {'files': {}}
    offset = 0
    for key, data in files.items():
        node = tree
        parts = key.split('/')
        for part in parts[:-1]:
            node = node['files'].setdefault(part, {'files': {}})
        node['files'][parts[-1]] = {'offset': str(offset), 'size': len(data)}
        offset += len(data)
    encoded = json.dumps(tree).encode()
    padded = encoded + b'\0' * (-len(encoded) % 4)
    header = struct.pack('<II', 4 + len(padded), len(encoded)) + padded
    path.write_bytes(struct.pack('<II', 4, len(header)) + header + b''.join(files.values()))


def framework(app, flags=b'11111111'):
    path = app / 'Contents/Frameworks/Electron Framework.framework/Electron Framework'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'framework fixture' + b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX' + bytes([1, len(flags)]) + flags)
    return path


class ToolingTest(unittest.TestCase):
    def test_beta_inspection_preserves_exact_version_commit_and_rejects_nightly(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / 'T3 Code (Beta).app'
            resources = app / 'Contents/Resources'
            resources.mkdir(parents=True)
            exe = app / 'Contents/MacOS/T3 Code (Beta)'
            exe.parent.mkdir()
            exe.write_bytes(b'signed-binary-fixture')
            with (app / 'Contents/Info.plist').open('wb') as f:
                plistlib.dump({'CFBundleExecutable': exe.name}, f)
            framework(app)
            package = {'version': '0.1.9', 't3codeCommitHash': 'a' * 40}
            for version, accepted in [('0.1.9', True), ('0.1.10-nightly.20261116.4761', False)]:
                package['version'] = version
                asar(resources / 'app.asar', {'package.json': json.dumps(package).encode()})
                if accepted:
                    result = tool.inspect_app(app)
                    self.assertEqual((result['version'], result['commit']), ('0.1.9', 'a' * 40))
                    self.assertEqual(result['executableSha256'], tool.sha256(exe))
                else:
                    with self.assertRaises(tool.Stop):
                        tool.inspect_app(app)

    def test_artifact_identity_or_file_changes_fail_before_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            folder = data / 'builds/0.1.9-test'
            folder.mkdir(parents=True)
            for name in ['inject.cjs', 'connect.mjs', 'overlay/apps/server/dist/bin.mjs',
                         'overlay/apps/server/dist/client/index.html', 'overlay/apps/desktop/dist-electron/boot.cjs',
                         'overlay/apps/desktop/dist-electron/main.cjs']:
                path = folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('checked artifact')
            app = {'app': '/fixture/Beta.app', 'version': '0.1.9'}
            manifest = {'schema': 1, 'build': folder.name, 'app': app,
                        'hashes': {str(p.relative_to(folder)): tool.sha256(p) for p in folder.rglob('*') if p.is_file()}}
            tool.atomic_json(data / 'current.json', manifest)
            args = types.SimpleNamespace(data_dir=str(data))
            for corrupt in ('app', 'file', 'added-file'):
                with self.subTest(corrupt=corrupt), patch.object(tool, 'inspect_app', return_value={**app, 'version': '0.1.10'} if corrupt == 'app' else app), patch.object(tool.subprocess, 'Popen') as spawn:
                    if corrupt == 'file':
                        (folder / 'inject.cjs').write_text('changed loader')
                    elif corrupt == 'added-file':
                        (folder / 'extra.cjs').write_text('unexpected loader')
                    reason = 'Official Beta changed' if corrupt == 'app' else 'inventory' if corrupt == 'added-file' else 'Staged build changed'
                    with self.assertRaisesRegex(tool.Stop, reason):
                        tool.launch(args)
                    spawn.assert_not_called()

    def test_disabled_or_missing_electron_fuses_prevent_any_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / 'Beta.app'
            resources = app / 'Contents/Resources'
            resources.mkdir(parents=True)
            exe = app / 'Contents/MacOS/Beta'
            exe.parent.mkdir()
            exe.write_bytes(b'official executable fixture')
            with (app / 'Contents/Info.plist').open('wb') as f:
                plistlib.dump({'CFBundleExecutable': 'Beta'}, f)
            asar(resources / 'app.asar', {'package.json': json.dumps({'version': '0.1.9', 't3codeCommitHash': 'a' * 40}).encode()})
            signed_framework = framework(app)
            metadata = tool.inspect_app(app)
            data = root / 'data'
            tool.atomic_json(data / 'current.json', {'build': 'test', 'app': metadata})
            for flags in [b'11101111', b'01111111', None]:
                with self.subTest(flags=flags):
                    if flags is None:
                        signed_framework.write_bytes(b'framework without fuse wire')
                    else:
                        framework(app, flags)
                    # Even after a staged artifact was accepted, the immediate pre-spawn read
                    # must catch a replacement app whose required startup fuse is disabled.
                    with patch.object(tool, 'validate_artifact', return_value=root / 'artifact'), patch.object(tool.subprocess, 'Popen') as spawn:
                        with self.assertRaisesRegex(tool.Stop, 'does not support'):
                            tool.launch(types.SimpleNamespace(data_dir=str(data)))
                        spawn.assert_not_called()

    def test_failed_patch_or_check_keeps_the_current_build(self):
        for failing in ('apply', 'focused-check'):
            with self.subTest(failing=failing), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                repo, source, data, cache = (root / x for x in ('repo', 'source', 'data', 'cache'))
                for p in (repo / 'patches', source, data):
                    p.mkdir(parents=True)
                (repo / 'patches/0001-feature.patch').write_text('patch fixture')
                (repo / 't3code-patches').write_text('tool fixture')
                (repo / 'checks.json').write_text(json.dumps({'commands': [{'cwd': '.', 'argv': ['focused-check']}]}))
                (source / 'package.json').write_text(json.dumps({'engines': {'node': '26.12.1'}, 'packageManager': 'pnpm@12.14.0'}))
                old = {'app': {'old': True}, 'recipe': 'previous', 'build': 'previous'}
                tool.atomic_json(data / 'current.json', old)
                args = types.SimpleNamespace(app='/fixture/Beta.app', data_dir=str(data), cache_dir=str(cache))
                @contextlib.contextmanager
                def checkout(*_):
                    yield source
                def run(argv, **_):
                    if failing in argv:
                        raise tool.Stop('expected failure')
                    return types.SimpleNamespace(returncode=0)
                with patch.object(tool, 'REPO', repo), patch.object(tool, 'inspect_app', return_value={'app': '/fixture/Beta.app', 'version': '0.1.9', 'commit': 'a' * 40}), patch.object(tool, 'source_checkout', checkout), patch.object(tool, 'ensure_node', return_value=root), patch.object(tool, 'run', run):
                    with self.assertRaises(tool.Stop):
                        tool.build(args)
                self.assertEqual(tool.read_json(data / 'current.json'), old)
                self.assertEqual(list((data / 'builds').iterdir()), [])

    def test_failed_injection_terminates_only_the_captured_process(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            folder = data / 'builds/test'
            folder.mkdir(parents=True)
            manifest = {'build': 'test', 'app': {'app': '/fixture/Beta.app', 'executable': '/fixture/Beta.app/Contents/MacOS/Beta'}}
            tool.atomic_json(data / 'current.json', manifest)
            child = types.SimpleNamespace(pid=12345, poll=lambda: None)
            child.terminate = unittest.mock.Mock()
            child.kill = unittest.mock.Mock()
            child.wait = unittest.mock.Mock()
            with patch.object(tool, 'validate_artifact', return_value=folder), patch.object(tool, 'inspect_app', return_value=manifest['app']), patch.object(tool.subprocess, 'Popen', return_value=child) as spawn, patch.object(tool.subprocess, 'run', return_value=types.SimpleNamespace(returncode=1)):
                with self.assertRaises(tool.Stop):
                    tool.launch(types.SimpleNamespace(data_dir=str(data)))
                env = spawn.call_args.kwargs['env']
                self.assertEqual(env['T3CODE_HOME'], str(data.resolve() / 't3'))
                self.assertEqual(env['T3CODE_PROFILE_DIRECTORY'], str(data.resolve() / 'electron'))
                self.assertEqual(env['T3CODE_DISABLE_AUTO_UPDATE'], 'true')
                self.assertIn('--user-data-dir=' + str(data.resolve() / 'electron'), spawn.call_args.args[0])
                child.terminate.assert_called_once_with()
                child.wait.assert_called_once_with(timeout=5)
                child.kill.assert_not_called()

    def test_node_archive_accepts_internal_links_and_rejects_external_links_on_python39(self):
        import io
        import tarfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for link, accepted in [('../lib/npm.js', True), ('../../../outside', False)]:
                archive_path = root / 'node.tar'
                with tarfile.open(archive_path, 'w') as archive:
                    data = b'node fixture'
                    regular = tarfile.TarInfo('node/lib/npm.js')
                    regular.size = len(data)
                    archive.addfile(regular, io.BytesIO(data))
                    symlink = tarfile.TarInfo('node/bin/npm')
                    symlink.type = tarfile.SYMTYPE
                    symlink.linkname = link
                    archive.addfile(symlink)
                destination = root / ('good' if accepted else 'bad')
                destination.mkdir()
                with tarfile.open(archive_path) as archive, patch.object(tool.tarfile, 'data_filter', None):
                    if accepted:
                        tool.extract_node(archive, destination)
                        self.assertEqual((destination / 'node/bin/npm').read_bytes(), data)
                    else:
                        with self.assertRaises(tool.Stop):
                            tool.extract_node(archive, destination)

    def test_checks_cannot_escape_the_source_checkout(self):
        for command in ({'cwd': '../other', 'argv': ['vp', 'test']}, {'cwd': '.', 'argv': 'vp test'}):
            with self.subTest(command=command), self.assertRaises(tool.Stop):
                tool.validate_checks({'commands': [command]})


if __name__ == '__main__':
    unittest.main()
