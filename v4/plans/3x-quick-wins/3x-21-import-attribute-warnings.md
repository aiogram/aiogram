# 3x-21 — Import- and attribute-level warnings for 4.0 removals

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [3x-20](3x-20-deprecation-machinery.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [3x-24](3x-24-migration-baseline-release.md), [3x-22](3x-22-registration-warnings.md) |
| Gate-conditional | no |
| Decisions | D12–D15, D42, D72, D74, R28, PD-13; 11 §1–§5 |
| Sources | [16 §1–2](../../research/16-support-policy.md), [11](../../research/11-removals.md), [README breaking changes 6, 10, 11](../../research/README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

16 §1 says warnings fire at the earliest point that has no runtime cost: at **import** for modules, and on **first
use** for names and attributes. This plan covers every 4.0 removal that can be detected that way, including the items
of the 3.x migration-baseline set (3x-20..3x-24): `UnsupportedKeywordArgument`, `Recommendation`, and `force_reply`
(verified below). Each warning
uses `warn_deprecated(<A-11 id>)` from 3x-20. aiogram's own code must never trigger one: the 3x-20 self-warning guard
fails the suite otherwise.

## Scope

**In.** Each item is (target → warning site → 3.x internal users that must switch to a private name first):

| # | Target | Site | Internal users to move off the public name |
|---|---|---|---|
| 1 | `aiogram.utils.markdown` (module) | import | `aiogram/types/user.py` (`from ..utils import markdown`; `User.mention_markdown` / `mention_html`) → use `text_decorations` or a private `_markdown` module |
| 2 | `aiogram.handlers` (package) | import | `aiogram/dispatcher/event/handler.py` imports `BaseHandler` for its `issubclass` check → replace with a lazy check that never imports the package. If `"aiogram.handlers.base"` isn't in `sys.modules`, no subclass can exist |
| 3 | `aiogram.utils.mixins` (module) | import | `aiogram/utils/i18n/core.py` (`ContextInstanceMixin`) → move the implementation to a private module |
| 4 | `aiogram.utils.deep_linking`: `create_telegram_link`, `encode_payload`, `decode_payload` re-exports | attribute (module `__getattr__`) | `deep_linking`'s own functions import them from `utils.link` / `utils.payload` |
| 5 | `aiogram.filters.BaseFilter` | attribute | — |
| 6 | `CancelHandler`, `REJECTED` (`aiogram/dispatcher/event/bases.py` and every re-export) | attribute | `router.py` / `error.py` internal references → private names |
| 7 | `UNSET_PARSE_MODE`, `UNSET_DISABLE_WEB_PAGE_PREVIEW`, `UNSET_PROTECT_CONTENT` (`aiogram.types.base`, re-exported from `aiogram.types`) | attribute | `aiogram/utils/media_group.py` (default arguments) → `Default("parse_mode")` etc. (11 §1) |
| 8 | `aiogram.exceptions.RestartingTelegram` | attribute | `aiogram/client/session/base.py` raises it → private alias; 3.x keeps raising it |
| 9 | `aiogram.exceptions.UnsupportedKeywordArgument` | attribute | `aiogram/dispatcher/event/telegram.py` raises it → private alias. 4.0 raises plain `TypeError` (11 §3) |
| 10 | `aiogram.utils.warnings.Recommendation` | attribute | `aiogram/dispatcher/event/handler.py` → private alias (11 §3: the warning goes in 4.0) |
| 11 | `ContentType` (`aiogram.enums`, `aiogram.types`) | attribute | `aiogram/types/message.py` imports it → `aiogram.enums.content_type.ContentType` directly |
| 12 | `Message.content_type` | first use (property) | — (check that no aiogram code calls it) |
| 13 | `MongoStorage` (`aiogram.fsm.storage.mongo`) | construction | — |
| 14 | `DefaultBotProperties` flat `link_preview_is_disabled` / `_prefer_small_media` / `_prefer_large_media` / `_show_above_text` | construction, only when a non-`None` value is passed (`__post_init__`) | `Default("link_preview_is_disabled")` lookups through `__getitem__` stay silent |
| 15 | `Dispatcher.__setitem__` / `__delitem__` (`dp["k"] = v`) | call | — (reads via `__getitem__` stay) |

`force_reply` (3x-20..3x-24 baseline item): **verify, don't warn.** 11 §4 calls `force_reply` on `as_markup` a leak through
`extra="allow"`. Bot API 10.4 (in 3.32) **added** `force_reply` to `InlineKeyboardMarkup` and
`ReplyKeyboardMarkup` (see `aiogram/types/inline_keyboard_markup.py` and #1954), so it is a real field now. Record
in Notes that 11 §4's item is stale and flag it to the owner. A-02 corrects the page, and A-11's entry is withdrawn
or never seeded.

**Out:**
- Registration and class-creation warnings (event_* parameters, class-based handlers, `TelegramMethod` subclasses,
  pydantic `CallbackData` features): 3x-22.
- Mutation and API-ledger fields: 3x-23.
- D100 positional calls: **no runtime warning**, checker only (I-18). Documented in 3x-24.

## Checklist

- [ ] For each row: move internal users first, then add the warning, then add the trigger to 3x-20's sync-test
      table, then wrap the existing tests that use the name in `pytest.warns`.
- [ ] Module-level warnings (rows 1–3) use `warnings.warn` at module top with the right `stacklevel` (the importer's
      frame). Test that `import aiogram` and `import aiogram.utils.i18n` emit nothing.
- [ ] Generated modules: `aiogram/enums/__init__.py` and `aiogram/types/__init__.py` are rewritten by butcher.
      Check that a hand-added module `__getattr__` survives `butcher apply all`. If it doesn't, apply the shim through
      `.butcher` config or the butcher tool, and record which.
- [ ] Row 12 lives in `message.py`. Check whether the `content_type` property is in a butcher-preserved hand-written
      block; if not, change it through `.butcher`.
- [ ] Row 14: warn only for explicitly passed flat fields. `DefaultBotProperties(link_preview=...)` stays silent.
- [ ] Docs: mark each item `.. deprecated::` with the replacement.
- [ ] Each row's entry exists in `registry.toml`, with `warn_3x.site` and `target` set to what this plan
      implemented. Add or adjust entries where A-11's seed differs; new ids come from the AG47xx block (A-11).
- [ ] 100% coverage. The full suite passes with the 3x-20 guard on.
- [ ] Changelog fragment `CHANGES/<pr>.removal.rst`: "Deprecated, removed in 4.0: …", listing the rows and their
      replacements.

## Acceptance criteria

- Each row emits exactly one `AiogramDeprecationWarning` carrying its registry id, at a user-code location
  (`warnings.catch_warnings(record=True)`, filename assertion).
- `python -W error::DeprecationWarning -c "import aiogram, aiogram.utils.i18n, aiogram.fsm.storage.memory"` exits 0.
- 3x-20's sync test passes: every implemented id has a trigger, and every trigger has an id.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Warn on every access of every mutable or removed thing at runtime, including hot paths | Warnings must have no runtime cost | 16 §1 |
| Deprecate `force_reply` on markups | It is a Bot API 10.4 field | 11 §4 is stale |
| Runtime warnings for positional calls (D100) | Would need a wrapper on every generated method and shortcut, costing time on every call | PD-02; checker-only (I-18) |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run --extra cli butcher apply all && git diff --exit-code
python -W error::DeprecationWarning -c "import aiogram, aiogram.utils.i18n"
```

## Workflow notes

- Parallel with 3x-22 and 3x-23 after 3x-20. They touch different files, except `dispatcher/event/handler.py`
  (rows 2 and 10 here; event_* parameters and class-based handlers in 3x-22), so land 3x-21 first.
- The 4.0 removals themselves happen in E-01 (dispatcher/filters), G-10 (utils), D-02 (exceptions), F-07 (Mongo)
  and D-01 (`DefaultBotProperties`).

## Notes
