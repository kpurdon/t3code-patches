# t3code-patches

Named thread groups and response font sizing for official T3 Code on macOS. A separate launcher loads the rebuilt JavaScript into the signed application.

Enable **Settings → Labs → Boring sidebar (group by project)** on desktop or web. Use the folder-plus button to create a named group. Right-click a thread and choose **Thread group** to create a group with that thread, move it to another group, or remove it from its current group. Each group can hold threads from several projects in the same T3 environment.

Click a group to collapse it. Its menu lets you rename or remove it. Removing a group puts its active threads back in their project folders. Pinned, snoozed, and settled threads use T3’s usual sections and return to their group when active again.

Groups are saved in the environment’s `settings.json`. Existing initiatives migrate with their names and members, including former project managers as ordinary members. The migration leaves the old `initiatives.json` file in place. Each browser profile remembers which folders are open.

Enable **Settings → Labs → The KP Experience → Enable response font sizing** to add **AI response font size** under **Appearance → Typography**. Choose 12–28 px with a live Markdown preview and reset to 14 px. It sizes assistant answers independently of the existing Interface font size; code blocks retain their code font size. Disabling hides the row and uses the Interface size again, retaining the chosen response size. These preferences are saved per device as `responseFontSizeEnabled` and `fontSizeResponse`.

## Build

Install Git and Python 3.9 or newer. From this checkout:

```sh
./t3code-patches nightly-update
./t3code-patches status
./t3code-patches install-launcher
```

Open the patched launcher from Spotlight or run `./t3code-patches launch`. Keep this checkout at a stable path because the launcher references it. The launcher uses the T3 and Chromium profiles under `~/.local/share/t3code-patches/`, including existing Patched Beta sessions. The running window belongs to the official app. Pin the launcher from Finder to the Dock to load the patches on subsequent launches.

Validated base: official Nightly `v0.1.12-nightly.20261125.5222` (`4da8d19d08ed`). For an exact validation build, use `nightly-update --version 0.1.12-nightly.20261125.5222` with a separate `--data-dir` placed before the command.

The updater downloads the matching official macOS release, verifies its digest and Apple signing identity, and stages the app in a versioned directory. It resolves the app's exact embedded source revision, applies `patches/*.patch`, runs `checks.json`, and builds the web, server, and desktop bundles. The loader uses the official app's native helpers and public T3 Connect settings. It requires the `RunAsNode` and startup-inspector Electron fuses.

## Updates

```sh
./t3code-patches autoupdate nightly
./t3code-patches autoupdate off
```

The hourly job follows official Nightly releases and uses the merged patch recipe from this repository's `main` branch. It checks and stages a matching app and overlay together. A failed update leaves the last working pair launchable. An already-running app keeps its current build until you quit and reopen it through the patched launcher.

Add `--maintenance-thread <thread-id>` after `autoupdate nightly` to send failures and recoveries to a dedicated thread in this T3 environment. The job holds messages locally when T3 is closed and retries on the next run. It reports a patch failure once per release and retries that patch when the merged recipe changes. The maintenance agent can prepare a repair PR for review. Logs and status are in `update.log`, `runtime.log`, and `nightly-status.json` in the installation directory.

## Development

Keep feature changes in the patch and their focused validation commands in `checks.json`. Tooling checks:

```sh
python3 -m unittest discover -s tests
node --check macos/connect.mjs
node --check macos/inject.cjs
```

The ASAR reader, build approach, and macOS loader are adapted from [btsouth/t3code-customize](https://github.com/btsouth/t3code-customize), under its MIT license (Copyright © 2026 Tyler South). This project does not include its stats patches or Tim's customization collection. T3 Code itself is [pingdotgg/t3code](https://github.com/pingdotgg/t3code), built from the revision embedded in the official app.
