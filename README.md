# t3code-patches

Focused initiative grouping patches for official T3 Code on macOS. The official application stays signed and unchanged; a separate launcher loads the rebuilt JavaScript into it.

Enable **Settings → Labs → The KP Experience → Enable initiative management** for each environment. It is off by default; turning it off keeps saved groups and sessions. The server setting is `initiativeManagementEnabled`.

Enable **Settings → Labs → The KP Experience → Enable response font sizing** to add **AI response font size** under **Appearance → Typography**. Choose 12–28 px with a live Markdown preview and reset to 14 px. It sizes assistant answers independently of the existing Interface font size; code blocks retain their code font size. Disabling hides the row and uses the Interface size again, retaining the chosen response size. These preferences are saved per device as `responseFontSizeEnabled` and `fontSizeResponse`.

The patch adds named, collapsible initiatives spanning repository projects in one T3 environment. Select a project manager, add execution sessions, and keep them together while working, idle, or snoozed. Settled sessions move into a collapsible Settled section inside their initiative; reopening restores their place in its active list. Archived and deleted sessions stay hidden; reopening an archived session restores its group. Headers summarize status with labeled counts. The shaded header collapses the group; a person icon marks the PM and tree connectors lead to its execution sessions. Use **Initiatives** in a session’s context menu to start a group with it as PM, or add, move, or remove its display membership. Choose **New thread…** from an initiative’s menu to select a project and create an empty session in that group. The session is saved immediately; an agent starts when you send its first message. Create initiatives from the top sidebar action row. Threads outside initiatives use compact rows above the groups, with their existing status headings. Use **Move up** or **Move down** in the initiative menu to set its sidebar order for this browser profile. **Settle initiative** settles its sessions and removes the group. Remove the group from its menu to keep sessions in their current state. The session’s **Initiatives** menu also lets you set an active thread as project manager.

The native `t3_initiative_list` and `t3_initiative_update` tools expose those same explicit relationships. New single and batch launches inherit their caller's display group; replaying a launch preserves subsequent moves and removals. A grouping failure returns `initiativeWarning` alongside the accepted launch, so repair the exact thread's display relationship rather than launching another one. UI groups do not adopt sessions into Builder or dispatcher's management registry.

Grouping is stored in `initiatives.json` beside the environment’s `settings.json` and shared across clients. Existing settings-based groups migrate on first load. Collapse is local to each browser profile. Project filters apply to the displayed members; hidden members stay recorded. Patched grouping controls appear only when the connected server advertises support. Mobile has no dedicated group UI in this patch.

## Build

Install Git and Python 3.9 or newer. From this checkout:

```sh
./t3code-patches nightly-update
./t3code-patches status
./t3code-patches install-launcher
```

Open the patched launcher from Spotlight or run `./t3code-patches launch`. Keep this checkout at a stable path because the launcher references it. The launcher uses the T3 and Chromium profiles under `~/.local/share/t3code-patches/`, including existing Patched Beta sessions. The running window belongs to the official app. Pin the launcher from Finder to the Dock to load the patches on subsequent launches.

Validated base: official Nightly `v0.1.12-nightly.20261124.5191` (`d7ae1e17915c`). For an exact validation build, use `nightly-update --version 0.1.12-nightly.20261124.5191` with a separate `--data-dir` placed before the command.

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
