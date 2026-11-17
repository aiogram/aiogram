# 17 — Built-in CLI (closes O8)

The current `aiogram-cli` 1.1.0 is a separate package and the `aiogram[cli]` extra. It is a proof of concept built on
click, click-plugins, colorama and watchfiles, with `version`, `plugins` and a `develop` runner (polling/webhook with
reload), plugins in the `aiogram_cli.plugins` entry-point group, and a pin to `aiogram<4`. 4.0 replaces it with a CLI
inside the package (D68).

| # | Decision |
|---|---|
| **D75** | **stdlib `argparse`, in core.** The `aiogram` console script and `python -m aiogram` are the same CLI and are always installed, with no new dependencies. Colours only on a TTY, honouring `NO_COLOR` |
| **D76** | **4.0 commands**: `run`, `migrate`, `info`, `bot` (§1) |
| **D77** | **Plugins** come from the new `aiogram.cli` entry-point group. The legacy `aiogram_cli.plugins` group is loaded too, with an `AiogramDeprecationWarning` for one window (D71), so commands registered there show up under `aiogram`. A final `aiogram-cli` release prints a notice to uninstall it and ships **no `aiogram` console script** (R30), so the two distributions never own the same script; the docs mention `pip install --force-reinstall aiogram` for broken upgrades. The CLI internals are argparse, so a plugin exposes `register(subparsers) -> None` plus a handler. The legacy click plugins run through a thin adapter, loaded only when click is installed; incompatible ones are reported (R30) |
| **D78** | **Reload** uses watchfiles through the `aiogram[reload]` extra. `--reload` without it exits with an install hint |

## 1. Commands

| Command | What it does |
|---|---|
| `aiogram run polling <module:attr>` | Resolves a `Dispatcher` (or a factory / coroutine returning one; default names `dp`, `dispatcher`), builds a `Runner` with a `Poller` (12) and runs it. Options: `--reload`, `--skip-updates` (drop pending updates on start), `--api URL` (local Bot API server), `--log-level`, `--log-format`, `--allowed-updates`. Multi-bot: `--token` / `$BOT_TOKEN` may be repeated or comma-separated |
| `aiogram run webhook <module:attr>` | Same resolution, serves the aiohttp webhook app (`--host`, `--port`, `--path`, `--secret-token`, `--set-webhook URL` to call setWebhook on start); token masking in access logs (D66, the CLI attaches the access-log filter, R22). Multi-bot needs an explicit `--bot TOKEN=PATH[:SECRET]` mapping per bot (R30) |
| `aiogram migrate fix\|check <paths>` | The D74 codemod (dry run by default) and checker (non-zero exit on findings); needs `aiogram[migrate]` |
| `aiogram info` | Versions of aiogram, the Rust core build, Python and implementation; free-threaded build and current GIL state; wheel tag; **installed optional packages** and their versions (installation metadata doesn't reveal which extras were requested, R30). Output is ready to paste into bug reports (`--json` available) |
| `aiogram bot me` | `getMe` + secondary usernames |
| `aiogram bot webhook info\|set\|delete` | Webhook management (`--drop-pending-updates`, `--secret-token`, `--max-connections`, `--allowed-updates`) |
| `aiogram bot commands sync <module:attr>` | Resolves the dispatcher and calls `dp.set_my_commands(bot)` (D60); `--dry-run` prints the `(scope, language) → commands` plan; `--delete-missing` covers the four fixed scopes × known languages plus an explicit `managed=[(scope, lang), …]` list (R30) |

- **Token**: `$BOT_TOKEN` or `--token-file PATH`. `--token` is accepted but warns that it ends up in shell history.
  Tokens are never echoed (D66).
- **Reload**: watchfiles restarts a child process on `*.py` changes (and `--reload-include` globs, e.g. `locales/**`).
  The child runs the normal Runner, so shutdown hooks fire.
- **Exit codes**: `0` ok, `1` runtime error, `2` usage error, `3` findings (`migrate check`).

## 2. Not in 4.0

Project scaffolding (`aiogram new`) and butcher commands. Butcher stays a contributor tool (`cargo xtask butcher`, 02).
Either can come later as a plugin or a built-in.
