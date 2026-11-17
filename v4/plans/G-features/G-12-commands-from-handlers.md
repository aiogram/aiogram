# G-12 — Bot commands from handlers (D60)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [E-04](../E-runtime/E-04-router-graph-multi-parent-flags.md), [E-09](../E-runtime/E-09-routing-keys-compiled-rejectors.md), [G-03](G-03-i18n-core.md) |
| Blocks | [G-18](G-18-cli-bot-commands.md) |
| Gate-conditional | no |
| Decisions | D60, D56, D114, R30, D25 |
| Sources | [06-utils.md §4 (D60)](../../research/06-utils.md), [19 R30](../../research/19-review-resolutions.md), [codex-review.md R30](../../research/codex-review.md), [17-cli.md §1](../../research/17-cli.md), [12-runtime.md §3](../../research/12-runtime.md), [03-routing.md §3](../../research/03-routing.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Bots repeat every command twice today: once in `Command("start")` and once in a hand-written `set_my_commands`
list. D60 (cf. PR #1867) derives the command menu from the handlers, so it cannot drift. Nothing is sent
automatically. The docs show the call in the per-bot `dp.bot_added` hook (12 §3).

## Scope

**In:**
- `Command(...)` (3.x `aiogram/filters/command.py`, `Command.__init__`) gains keyword-only:
  - `description: str | None = None`;
  - `scope: BotCommandScope | None = None` (default scope when `None`);
  - `language_code: str | None = None`;
  - `description_key: str | None = None`, an i18n key (D25) for localised descriptions. With it, one entry is
    produced per `core.available_locales` (G-03), each with the matching `language_code`.
- Only **plain string** commands can carry a description. A `description=` with a regex pattern raises `ValueError`
  at construction.
- The new kwargs must not disqualify the filter from E-09's command index / compiled rejectors. Add an agreement test
  case.
- `router.resolve_bot_commands() -> dict[tuple[BotCommandScope, str | None], list[BotCommand]]` walks the tree,
  including multiple parents (D56); a router reachable twice is visited once.
- `await dp.set_my_commands(bot, *, delete_missing=False, managed=())`:
  - calls `setMyCommands` for each `(scope, language)`;
  - with `delete_missing=True`, calls `deleteMyCommands` for the four fixed scopes (`BotCommandScopeDefault`,
    `AllPrivateChats`, `AllGroupChats`, `AllChatAdministrators`) × known languages, plus every `(scope, lang)` in
    `managed`, that has no commands in the resolved plan (19 R30);
  - returns the plan it applied, so the CLI's `--dry-run` (G-18) can print it.
- `CommandStart` and commands with `description=None` are excluded (D60).

**Out:**
- The CLI `aiogram bot commands sync`: G-18.
- Automatic sync on start: rejected (D60, "nothing is sent automatically").

## Checklist

- [ ] `Command` kwargs + validation; `CommandStart` keeps its signature.
- [ ] `resolve_bot_commands()` over the live router graph.
- [ ] `set_my_commands()` with `delete_missing` / `managed`, returning the applied plan.
- [ ] **Decide how conflicting descriptions are handled** (same command, same scope + language, different
      descriptions in two routers). Proposed default: raise `ValueError` naming both handlers; identical duplicates
      are deduplicated silently. Record in Notes and flag to owner.
- [ ] **Decide command order** (proposed default: DFS registration order of the router tree, first occurrence wins
      the position) — record in Notes.
- [ ] **Decide what "known languages" means for `delete_missing`** (proposed default: the union of languages in the
      resolved plan, `None` (no language), and `core.available_locales` when an i18n core is installed; anything
      else must be listed in `managed`). Record in Notes and flag to owner.
- [ ] **Decide whether `resolve_bot_commands` reads the live graph or a snapshot** (proposed default: the live
      router graph, since the CLI and `bot_added` hooks may run without a compiled snapshot; the result is
      deterministic for a given graph). Record in Notes.
- [ ] **Decide whether `CommandStart(description=…)` opts in** (R30; proposed default: yes; `CommandStart` is
      excluded only when no description is given). Record in Notes and flag to owner.
- [ ] Docs: "Bot commands" page with the `bot_added` example and a `delete_missing` warning.
- [ ] Tests (100% coverage of new code): MockedBot asserting the exact `setMyCommands` / `deleteMyCommands` calls for a
      multi-router, multi-language, multi-scope tree; diamonds across dispatchers; regex + description error.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- For a fixture tree (3 routers, 5 commands, 2 scopes, 2 locales via a gettext core), `set_my_commands` issues
  exactly the expected calls in a stable order. Running it twice produces the same calls.
- `delete_missing=True` never deletes a `(scope, lang)` outside the four fixed scopes × known languages and `managed`.
- The E-09 rejector agreement matrix includes `Command("x", description="…")` and still passes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Sync automatically at start | Unexpected API calls; per-bot setup belongs in `bot_added` | D60, 12 §3 |
| Deleting every remote scope | Needs an inventory the app does not have | 19 R30 |
| Descriptions on regex commands | No concrete command name to advertise | D60 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: E-04 (multi-parent graph walk), E-09 (rejectors must keep indexing `Command`), G-03 (`available_locales`,
  `i18n.get`).
- Output: G-18 uses `resolve_bot_commands` / `set_my_commands`. H-17 may add a toolkit assertion helper.

## Notes
