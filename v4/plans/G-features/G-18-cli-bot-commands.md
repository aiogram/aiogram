# G-18 — `aiogram bot` commands (me, webhook, commands sync)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-15](G-15-cli-core.md), [G-12](G-12-commands-from-handlers.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | D76, D60, D66, R30 |
| Sources | [17-cli.md §1](../../research/17-cli.md), [06-utils.md §4 (D60)](../../research/06-utils.md), [19 R30](../../research/19-review-resolutions.md), [codex-review.md R30](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Small operational tasks shouldn't need a script: checking which bot a token belongs to, inspecting or resetting a
webhook, pushing the command menu derived from handlers (D60).

## Scope

**In:**
- `aiogram bot me`: `getMe` plus secondary usernames. Text and `--json`.
- `aiogram bot webhook info|set|delete`:
  - `info` → `getWebhookInfo`, with the URL shown (the URL carries no token);
  - `set URL` with `--secret-token`, `--max-connections`, `--allowed-updates`, `--drop-pending-updates`;
  - `delete` with `--drop-pending-updates`.
- `aiogram bot commands sync <module:attr>`:
  - resolves the dispatcher (G-16 resolver; shared helper in G-15 if G-16 is not merged; record where it lives) and
    calls `dp.set_my_commands(bot, …)` (G-12);
  - `--dry-run` prints the `(scope, language) → commands` plan and makes no API call;
  - `--delete-missing` and `--managed SCOPE[:LANG]` (repeatable) map to G-12's `delete_missing` / `managed`.
- Token handling via the G-15 helper. Nothing echoes the token. The `--api URL` local server is supported.
- Exit codes per G-15. A Telegram API error prints the redacted message and `e.reason` (D47) and exits `1`.

**Out:**
- `resolve_bot_commands` / `set_my_commands`: G-12.
- Webhook serving: G-16.

## Checklist

- [ ] `bot me`, `bot webhook info|set|delete`, `bot commands sync`.
- [ ] `--dry-run` plan output: deterministic order (G-12's order decision), stable text and `--json`.
- [ ] **Decide the `--managed` scope syntax** (proposed default: `default`, `all_private_chats`, `all_group_chats`,
      `all_chat_administrators`, `chat:<id>`, `chat_administrators:<id>`, `chat_member:<id>:<user_id>`, with an
      optional `:<lang>` suffix). Record in Notes.
- [ ] Docs: CLI reference entries + "Bot commands" page cross-link.
- [ ] Tests (100% coverage of new code): MockedBot-backed in-process runs asserting the exact API calls; dry-run makes
      zero calls; API errors map to exit `1` with no token in output.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- `aiogram bot commands sync app:dp --dry-run` prints a plan identical to `dp.set_my_commands`'s returned plan for the
  G-12 fixture tree, with zero API calls recorded.
- `aiogram bot webhook set https://x/y --secret-token S --drop-pending-updates` issues one `setWebhook` with exactly
  those parameters.
- No test output contains the token.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Deleting all remote command scopes on `--delete-missing` | Needs an inventory the app does not have | 19 R30 |
| Printing the full token in `bot me` | Token redaction on by default | D66 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: G-15 (plugin API, token helper), G-12 (commands plan), the G-16 resolver (or a shared helper).
- Can run in parallel with G-16 and G-19.

## Notes
