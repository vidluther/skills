---
name: herdr
description: Drive or customize the Herdr desktop app (spaces, tabs, panes, layouts, keys, settings, mods) and run or coordinate agents and programs in herdr-core (`hc`). Use when the user mentions Herdr, herdr-app, hc, herdr-core, or asks to open/split/focus a tab or pane, rebind a Herdr key, change a Herdr layout or theme, write a Herdr mod, or start, read, message, or wait on an agent in a persistent terminal.
---

# Herdr

Herdr ships its own agent manuals, versioned with the installed app. Load them at the start of the task instead of relying on memory — they change between releases.

| Task | Read first |
| --- | --- |
| Change what the person sees: spaces, tabs, panes, focus | `herdr-app --skill` |
| Customize keys, settings, layouts, themes, or mods | `herdr-app --skill`, then `~/.config/herdr-app/AGENTS.md` (or `$HERDR_APP_HOME/AGENTS.md`) |
| Start, read, message, wait on, or clean up agents and programs | `hc --skill` |

Both manuals apply when a task spans them (e.g. start an agent with `hc` and show it in a new tab).

## Ground rules

- Inspect before acting: `herdr-app ls`, `herdr-app status`, `herdr-app commands`. Never launch bare `herdr-app` to inspect — it opens or raises the window.
- Never stop, signal, or restart the person's app or core (`hc server stop`) unless asked.
- Don't edit `AGENTS.md`, the `.d.ts` files, `frame/`, or shipped layouts/mods — the app rewrites them. Clone first (`layout.clone`, `mod.clone`).
- After editing keys, settings, or layouts, check `herdr-app status` and any `*.error` file. After a mod change, `herdr-app check <mod folder>` must pass and `herdr-app shot` must look right before calling it done.
- `~/.config/herdr-app/keys.json` and `settings.json` are the person's own files; the Settings screen rewrites `settings.json`, so don't replace it with a symlink.
- Only clean up terminals you started.
