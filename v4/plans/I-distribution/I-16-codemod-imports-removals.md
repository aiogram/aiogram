# I-16 — Codemod and checker rules: imports and legacy removals

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-14](I-14-migrate-engine.md), [C-26](../C-butcher/C-26-removal-inventory-signature-table.md), [G-10](../G-features/G-10-utils-removals.md), [G-20](../G-features/G-20-aiogram-i18n-final-release.md) |
| Blocks | [I-20](I-20-examples-port-smoke.md), [I-22](I-22-migration-rehearsal.md), [I-23](I-23-beta-pre-release.md) |
| Gate-conditional | no |
| Decisions | D12, D13, D42, D47, D74, 11 §1–5, R28 |
| Sources | [11-removals.md](../../research/11-removals.md), [16-support-policy.md §2.2](../../research/16-support-policy.md), [README breaking changes 6, 10, 11](../../research/README.md), [codex-review R28](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

11-removals lists the compat code that 4.0 deletes. Most uses are mechanical renames that a codemod can rewrite safely
(16 §2.2). The rest must be reported with a pointer to the guide. Each rule's id is the registry id seeded by A-11
(PD-13) and must match the warning that 3x-21 / 3x-22 emit on the migration-baseline 3.x release, so the user sees the
same `AG4xxx` in both places.

## Scope

**In.** Rules on the I-14 engine. The finding class is in brackets; the 3.x source of each symbol is named.

| Rule | 3.x symbol | Action | Class |
|---|---|---|---|
| ContentType filters | `aiogram.enums.ContentType`, `Message.content_type` | `F.content_type == ContentType.PHOTO` → `F.photo`; `F.content_type.in_({...})` / `.in_([ContentType.TEXT, ...])` → `F.text \| F.sticker`; any other `content_type` / `ContentType` use is reported | definite fix / definite report |
| event_from_user & co. | `event_from_user`, `event_chat`, `event_thread_id` handler kwargs (`dispatcher/middlewares/user_context.py`) | handler/middleware parameter `event_from_user: User` → `event_context: EventContext`, and its uses → `event_context.user` (`.chat`, `.thread_id`); `data["event_from_user"]` in middlewares → `data["event_context"].user` | definite where the function signature is local, else report |
| utils.markdown | `aiogram/utils/markdown.py` (`hbold`, `hitalic`, `text`, `bold`, …) | → `aiogram.utils.formatting` nodes or `html.bold(html.quote(x))` where a 1:1 mapping exists (table in the rule); the rest are reported | definite for the mapped functions, heuristic for `text(...)` joins |
| BaseFilter | `aiogram.filters.BaseFilter` (= `Filter`) | → `Filter` | definite |
| UNSET sentinels | `UNSET_PARSE_MODE`, `UNSET_DISABLE_WEB_PAGE_PREVIEW`, `UNSET_PROTECT_CONTENT` (`aiogram/types/base.py`) | → `Default("parse_mode")`, `Default("link_preview_is_disabled")` → report (the `link_preview` default name changes), `Default("protect_content")` | definite / report |
| Flat link-preview defaults | `DefaultBotProperties(link_preview_is_disabled=..., link_preview_prefer_small_media=..., …)` (`aiogram/client/default.py`) | → `link_preview=LinkPreviewOptions(is_disabled=..., ...)` | definite when all args are keywords on the constructor |
| deep_linking re-exports | `from aiogram.utils.deep_linking import create_telegram_link / encode_payload / decode_payload` | → `aiogram.utils.link` / `aiogram.utils.payload` | definite |
| `create_channel_bot_link(parameter=…)` | `aiogram/utils/link.py` | report (parameter removed) | definite report |
| RestartingTelegram | `aiogram.exceptions.RestartingTelegram` | `except RestartingTelegram` → `except TelegramServerError` (reason via `e.reason`, D47) | definite |
| CancelHandler / REJECTED | `aiogram.dispatcher.event.bases` | report (no replacement; never raised / returned) | definite report |
| `dp[...] = ...` / `del dp[...]` | `Dispatcher.__setitem__` / `__delitem__` | report, suggest `Dispatcher(**kw)` / `workflow_data` before start | definite when the receiver infers to `Dispatcher`, else heuristic |
| MongoStorage | `aiogram.fsm.storage.mongo.MongoStorage` (motor) | report; suggest `PyMongoStorage` with a pymongo `AsyncMongoClient` (not a drop-in: client type changes) | definite report |
| utils.mixins | `ContextInstanceMixin`, `DataMixin` | report | definite report |
| Removed Bot API fields/entities (ledger reset) | the 122 fields + `KeyboardButtonRequestUser`, `UserShared`, `StoryAreaPosition` (C-26 inventory) | keyword args / attribute reads of removed names: report with the replacement from the ledger (`reply_to_message_id` → `reply_parameters=ReplyParameters(message_id=...)`, `disable_web_page_preview` → `link_preview_options`); a mechanical fix only where the ledger `replacement` gives a 1:1 mapping | definite report; definite fix for 1:1 |
| `from magic_filter import F` | `Recommendation` warning removed (11 §3) | no finding (docs note only) | — |
| `aiogram_i18n` imports (README breaking change 14) | `import aiogram_i18n` / `from aiogram_i18n import …` | report with a link to the "Migrating from aiogram_i18n" mapping page; uses the registry id G-20 allocates | definite report |

**Out:**
- Class-based handlers and `CallbackData` pydantic features (I-19, heuristic).
- Model semantics (I-17).
- Positional calls (I-18).
- `force_reply` on `as_markup`: no rule. It is a real Bot API 10.4 field (#1954) and is not removed (11 §4 is stale).

## Checklist

- [ ] One module per rule group under `aiogram/migrate/rules/` (`content_type.py`, `event_context.py`, `markdown.py`,
      `removals.py`, `ledger.py`).
- [ ] Each rule uses the registry id from A-11's seed. Where the seed lacks one, add the entry through A-11's allocation
      process (append-only) and record it in Notes.
- [ ] The markdown mapping table, verified against the 3.x `aiogram/utils/markdown.py` public functions (every public
      function is either mapped or explicitly "report").
- [ ] The ledger rule reads C-26's removal inventory by path.
- [ ] `aiogram_i18n` import rule: report with the G-20 registry id and the mapping-page link.
- [ ] Golden tests per rule (`before/after`) plus report-only cases. Cover import aliases
      (`from aiogram.utils import markdown as md`, `import aiogram.enums as e`).
- [ ] Set the registry codemod-coverage field (✔ / partial / ✖) for each entry. The I-12 check enforces consistency.
- [ ] Run all rules over the 3.x `examples/` and `docs/**/*.rst` code blocks extracted by a small script; triage false
      positives in Notes.
- [ ] Tests (100% coverage of the rule modules).
- [ ] Changelog fragment `CHANGES/<id>.feature.rst` (migrate rules for removed APIs). The registry entries are A-11's
      seed, updated here.

## Acceptance criteria

- Every item in 11-removals §1–5 marked **remove** has a rule or an explicit "no finding" line in this plan's table.
  A test compares the rule ids against the registry `removal-4.0` entries tagged area `removals`.
- Golden tests pass. `fix` never produces code that fails `compile()`, which is checked for every golden `after`.
- A fixture importing `aiogram_i18n` (plain and `from` forms, aliased) gets one report per import carrying G-20's
  registry id and the mapping-page URL.
- On the 3.x `examples/` tree, `check` reports the 9 `utils.markdown` uses in 3 files (11 §4), each with a fix or a report.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rewriting `MongoStorage` → `PyMongoStorage` automatically | Client type differs (motor vs pymongo async); not mechanical | 11 §5, R28 |
| Keeping `utils.markdown` as a deprecated shim | Removed | D13 |
| Keeping deprecated Bot API fields one more window | 4.0 ledger reset is an explicit exception to D71 | 02 §4, R28 |

## Validation

```bash
make dev
uv sync --extra migrate
uv run pytest tests/test_migrate -q
uv run pytest tests
uv run mypy aiogram
uv run python scripts/migration_registry.py check
make lint
```

## Workflow notes

- Inputs: I-14 (engine), C-26 (removal inventory), G-20 (the `aiogram_i18n` registry id and mapping page).
- Ids must match 3x-21 / 3x-22 warnings. Both read the same `registry.toml` ids from A-11.
- Runs in parallel with I-17, I-18 and I-19.

## Notes

(empty)
