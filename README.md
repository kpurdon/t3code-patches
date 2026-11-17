# t3code-patches

Focused initiative grouping patches for the official T3 Code Beta on macOS. The official application stays signed and unchanged; a separate launcher loads the rebuilt JavaScript into it.

The patch adds named, collapsible initiatives spanning repository projects in one T3 environment. Select a project manager, add execution sessions, and keep them together while working, idle, or snoozed. Settled sessions move into a collapsible Settled section inside their initiative; reopening restores their place in its active list. Headers summarize status with labeled counts. The shaded header collapses the group; a person icon marks the PM and tree connectors lead to its execution sessions. Use **Initiatives** in a session’s context menu to start a group with it as PM, or add, move, or remove its display membership. Choose **New thread…** from an initiative’s menu to select a project and create an empty session in that group. The session is saved immediately; an agent starts when you send its first message. Create initiatives from the top sidebar action row. Threads outside initiatives use compact rows above the groups, with their existing status headings. Removing a group keeps every session.

The native `t3_initiative_list` and `t3_initiative_update` tools expose those same explicit relationships. New single and batch launches inherit their caller's display group; replaying a launch preserves subsequent moves and removals. A grouping failure returns `initiativeWarning` alongside the accepted launch, so repair the exact thread's display relationship rather than launching another one. UI groups do not adopt sessions into Builder or dispatcher's management registry.

Grouping is stored in `initiatives.json` beside the environment’s `settings.json` and shared across clients. Existing settings-based groups migrate on first load. Collapse is local to each browser profile. Project filters apply to the displayed members; hidden members stay recorded. Patched grouping controls appear only when the connected server advertises support. Mobile has no dedicated group UI in this patch.

## Build

Install the official Beta, Git, and Python 3.9 or newer. From this checkout:

```sh
./t3code-patches build
./t3code-patches status
./t3code-patches install-launcher
```

Open **T3 Code (Patched Beta)** from Spotlight, or run `./t3code-patches launch`. It uses separate T3 and Chromium profiles under `~/.local/share/t3code-patches/`; it does not import or resume existing sessions. Keep the repository checkout at a stable path because the launcher references it.

Validated base: official Beta `v0.1.9` (`24e77473ecf41bc1f7142529c7911c1c1aae1d76`). Future releases must pass the patch, checks, and build again.

The build reads Beta's exact source revision from its installed archive, applies `patches/*.patch`, installs frozen upstream dependencies, runs `checks.json`, and builds the web, server, and desktop bundles. It downloads the exact upstream Node version when needed, verified against Node's published checksum. Native helpers and public T3 Connect settings come from your official app.

For a different app location or storage directory, put options before the command:

```sh
./t3code-patches --app '/path/to/T3 Code (Beta).app' --data-dir '/path/to/patch-data' build
```

## Updates

After updating the official Beta, run `./t3code-patches update`. Optional hourly checks, also triggered when the Beta app changes:

```sh
./t3code-patches autoupdate on
./t3code-patches autoupdate off
```

The background job builds and stages only. It never starts or quits T3, ports patches with an agent, edits this repository, or pushes code. It builds the patches in the local checkout; pull reviewed repository updates yourself. Automatic app updates are disabled while the patched app is running, so update the official Beta separately.

The loader requires Beta's `RunAsNode` and startup-inspector Electron fuses. It checks both before starting any process; incompatible Betas stop without falling back to stock.

A failed patch, check, or build leaves the prior artifact intact. Launch refuses an artifact for a different official Beta or modified bundle. Restart through the patched launcher after a successful update; there is no fallback that silently opens the stock app against shared data. Logs are local: `~/.local/share/t3code-patches/update.log` and `runtime.log`.

## Stone theme

`themes/stone.json` adapts Stone's warm gray terminal palette for the app: brighter text, distinct sage surfaces, blue selection and action colors, and richer status accents. The terminal background and foreground retain the original Stone values. Install it into the running patched environment with:

```sh
t3 theme set ./themes/stone.json --id stone
```

In Settings → Appearance, set Glass opacity to 100% for solid surfaces. Theme changes apply live and do not require rebuilding or restarting the app.

## Development

Keep feature changes in the patch and their focused validation commands in `checks.json`. Tooling checks:

```sh
python3 -m unittest discover -s tests
node --check macos/connect.mjs
node --check macos/inject.cjs
```

The ASAR reader, build approach, and macOS loader are adapted from [btsouth/t3code-customize](https://github.com/btsouth/t3code-customize), under its MIT license (Copyright © 2026 Tyler South). This project does not include its stats patches or Tim's customization collection. T3 Code itself is [pingdotgg/t3code](https://github.com/pingdotgg/t3code), built from the revision embedded in your installed app.
