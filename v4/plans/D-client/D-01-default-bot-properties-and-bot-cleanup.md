# D-01 — Frozen `DefaultBotProperties`, `Bot` cleanup, `Bot.__repr__`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-11](../A-contracts/A-11-migration-registry.md), [C-15](../C-butcher/C-15-bot-methods-emitter.md) |
| Blocks | [D-07](D-07-rust-encoder-json.md), [D-11](D-11-session-on-new-codec.md), [D-14](D-14-webhook-reply-encoding.md) |
| Gate-conditional | no |
| Decisions | PD-20, D66, 11 §2, R18 (defaults mutation contract) |
| Sources | [11-removals.md §2](../../research/11-removals.md), [05-network.md §2.1, §2.5](../../research/05-network.md), [15-observability.md §5](../../research/15-observability.md), [codex-review.md R18](../../research/codex-review.md), [19](../../research/19-review-resolutions.md), [plans README §1](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The Rust encoder (D-07) resolves `Default("…")` sentinels against a per-bot defaults snapshot that is "converted to
a Rust struct once per bot" (05 §2.1). Codex R18 pointed out that a mutable `DefaultBotProperties` makes that
snapshot stale. PD-20 resolves it: `DefaultBotProperties` becomes **frozen**. The same file carries 3.x compat
leftovers that 11 §2 removes, and 15 §5 requires `Bot.__repr__` to show only the bot id (no token).

## Scope

**In:**
- `aiogram/client/default.py`:
  - `DefaultBotProperties` → `@dataclass(slots=True, kw_only=True, frozen=True)`.
  - Remove the flat `link_preview_is_disabled`, `link_preview_prefer_small_media`, `link_preview_prefer_large_media`,
    `link_preview_show_above_text` fields, the `__post_init__` that folds them into `link_preview`, and `__getitem__`.
    Only `link_preview: LinkPreviewOptions | None` remains; `Default(...)` names follow (11 §2).
  - `Default` sentinel class stays (Python-visible, 01 §3.3).
  - A cached, read-only accessor the encoder will consume (e.g. `DefaultBotProperties._resolved()` returning a plain
    `dict[str, Any]` of set values, computed once per instance). D-07 converts it to the Rust struct; this task only
    provides the Python side.
- `aiogram/client/bot.py` (`Bot` class):
  - Remove `**kwargs` from `Bot.__init__` and the "removed in 3.7.0" `TypeError` block.
  - Compute `bot.id` once at init (05 §2.5) instead of `extract_bot_id(self.__token)` on every access.
  - Add `Bot.__repr__` → `Bot(id=<id>)`; never includes the token (15 §5, D66).
- The only caller of `bot.default[...]` (`aiogram/client/session/base.py` `BaseSession.prepare_value`) switches to
  attribute access / the accessor.
- **`UNSET_*` sentinel removal (owned here, 11 §1):** delete `UNSET_PARSE_MODE`, `UNSET_DISABLE_WEB_PAGE_PREVIEW` and
  `UNSET_PROTECT_CONTENT` from `aiogram/types/base.py`, drop the `UNSET_PARSE_MODE` export from `aiogram/types`
  (`__init__.py` import and `__all__`), swap `aiogram/utils/media_group.py` (its eight `parse_mode=UNSET_PARSE_MODE`
  defaults) and any other in-tree use to the matching `Default("…")`, and remove
  the sentinel cases in `tests/test_api/test_client/test_session/test_base_session.py` (and
  `tests/test_api/test_client/test_default.py`, if any).
- Remove compat-only tests named in 11 §7 (bot-kwargs cases in `tests/test_api/test_client/test_bot.py`, the flat
  link-preview cases in `tests/test_api/test_client/test_default.py`).

**Out:**
- Rust defaults struct and resolution in the encoder → D-07.
- Token-safe exception text → D-03. Logging redaction filter → H-02.
- `MediaGroupBuilder`'s generated `parse_mode=Default("parse_mode")` signatures and their registry entry → G-11.

## Checklist

- [ ] Freeze `DefaultBotProperties` (PD-20); assignment raises `dataclasses.FrozenInstanceError`.
- [ ] Remove flat `link_preview_*` fields, `__post_init__` folding and `__getitem__`.
- [ ] Add the cached resolved-defaults accessor; document it as internal (underscore).
- [ ] Decide whether reassigning `bot.default = DefaultBotProperties(...)` is supported (proposed default: yes; the
      encoder snapshot is keyed by the identity of the `DefaultBotProperties` object, so reassignment is picked up on
      the next call) — record in Notes and flag to owner.
- [ ] Remove `Bot.__init__(**kwargs)` and the 3.7.0 `TypeError` block.
- [ ] Cache `bot.id` at init.
- [ ] `Bot.__repr__` returns `Bot(id=…)`; test that `repr(bot)` and `str(bot)` never contain the token.
- [ ] Update the in-tree caller of `default[...]` (`BaseSession.prepare_value`).
- [ ] Remove the `UNSET_*` sentinels, their `aiogram.types` export and their test cases.
- [ ] Tests (100% coverage of new code).
- [ ] Migration-registry entries (PD-13, `aiogram/_migration/registry.toml`, kind `removal-4.0`): frozen
      `DefaultBotProperties`; flat `link_preview_*` fields; `Bot(**kwargs)`; the three `UNSET_*` sentinels (replacement
      `Default("parse_mode")` / `Default("protect_content")` / `link_preview=`).
- [ ] Changelog fragment(s) in `CHANGES/` (category `removal`).

## Acceptance criteria

- `DefaultBotProperties(parse_mode="HTML").parse_mode = "X"` raises `FrozenInstanceError`.
- `DefaultBotProperties(link_preview_is_disabled=True)` raises `TypeError` (unknown kwarg).
- `Bot("42:TEST…", parse_mode="HTML")` raises `TypeError` (no `**kwargs`).
- `repr(Bot(token))` equals `f"Bot(id={bot.id})"`; a test with a fabricated token asserts the token substring is
  absent from `repr`/`str`.
- `from aiogram.types import UNSET_PARSE_MODE` raises `ImportError`; `grep -rn "UNSET_PARSE_MODE\|UNSET_PROTECT_CONTENT\|UNSET_DISABLE_WEB_PAGE_PREVIEW" aiogram/`
  returns nothing.
- `bot.id` is read from an attribute set in `__init__` (no token parsing per access).
- Registry entries exist and validate against the A-11 schema.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep `DefaultBotProperties` mutable and rebuild the Rust snapshot on every call | Pays conversion per request; hides a stale-snapshot class of bugs | PD-20 |
| Keep mutable and document mutation as unsupported | Silent staleness; frozen makes it an error | PD-20 |
| Keep flat `link_preview_*` fields as deprecated aliases | Compat shim from 3.4; 4.0 resets compat | 11 §2 |

## Validation

```bash
make dev
uv run pytest tests/test_api/test_client
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Input: C-15's generated `_BotMethods` mixin, which the cleaned-up `Bot` inherits.
- Output consumed by D-07 (defaults snapshot), D-11 (`Bot.__call__` path), D-14 (webhook reply defaults).
- Parallel with D-02..D-06.

## Notes
