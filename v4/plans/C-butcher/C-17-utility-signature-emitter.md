# C-17 — Builder and utility signature emitter (D59)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-09](C-09-resolution-passes.md) |
| Blocks | [G-11](../G-features/G-11-generated-utils-signatures.md), [C-23](C-23-check-offline-determinism.md) |
| Gate-conditional | no |
| Decisions | D59, D116, D100, D15, PD-02 |
| Sources | [06-utils.md §4](../../research/06-utils.md), [11-removals.md §1, §4](../../research/11-removals.md), [19 D116](../../research/19-review-resolutions.md), `aiogram/utils/keyboard.py`, `aiogram/utils/media_group.py`, `aiogram/utils/chat_action.py`, `aiogram/utils/formatting.py` (3.x) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

These utilities copy type fields by hand today and drift on every Bot API bump:
- `InlineKeyboardBuilder.button()` / `ReplyKeyboardBuilder.button()` in `aiogram/utils/keyboard.py`;
- `MediaGroupBuilder.add_audio/add_photo/add_video/add_document` in `aiogram/utils/media_group.py`, still defaulting to `UNSET_PARSE_MODE`;
- `ChatActionSender.typing()/upload_photo()/…` in `aiogram/utils/chat_action.py`;
- `Text.as_caption_kwargs()/as_poll_question_kwargs()/as_poll_explanation_kwargs()/as_gift_text_kwargs()` in `aiogram/utils/formatting.py`.

D59 generates their **signatures and docs** from the IR. The runtime bodies delegate to the type constructors.
Album aggregation was withdrawn (D116) and is not part of this.

## Scope

**In:** `crates/butcher/src/emit/utils.rs`. It emits generated mixin modules that the hand-written classes inherit from:
- `aiogram/utils/_generated/keyboard.py`: `button(self, *, text: str, url: str | None = None, …)` for the
  `InlineKeyboardButton` and `KeyboardButton` fields; body `return self._button(**locals_without_self)`.
- `aiogram/utils/_generated/media_group.py`: one `add_<kind>(self, *, media, caption=None, parse_mode=Default("parse_mode"), …)` per `InputMedia*` member of the media-group union. `UNSET_PARSE_MODE` is gone (11 §1).
- `aiogram/utils/_generated/chat_action.py`: one classmethod constructor per `ChatAction` enum member.
- `aiogram/utils/_generated/formatting.py`: one `Text.as_<x>_kwargs()` per IR triple `X` / `X_entities` / `X_parse_mode` (this emitter owns the triple detection over all IR methods and types), plus a generic `as_kwargs_for(self, field: str)`.
- All keyword-only (D100). Docstrings come from the IR field docs.

**Out:** rewiring the hand-written classes to inherit the mixins and the runtime bodies (G-11); album aggregation (D116).

## Checklist

- [ ] **Decide the generated module shape together with G-11** (proposed default: generated Python **mixin** modules
  under `aiogram/utils/_generated/`, inherited by the hand-written classes; no `.pyi`-only signatures, so runtime
  `inspect.signature` matches the types). Record it in Notes and flag it to the owner.
- [ ] Emitters for the four mixins; triple detection (`X`, `X_entities`, `X_parse_mode`) over all IR methods.
- [ ] Test: the triples found at 10.4 cover at least the fields behind today's hand-written helpers (`text` for `as_kwargs`, `caption`, `question`, `explanation`, gift `text`). The full emitted list is pinned in the test, so a new triple shows up as a reviewed diff.
- [ ] Test: `button()` params equal the button type's constructor params; `add_<kind>` covers every media-group union member.
- [ ] Migration-registry entry (PD-13): the `UNSET_*` removal entry is D-01's (11 §1); positional → keyword for these utilities (D100). Changelog fragment.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- After G-11 wires them in, `tests/test_utils/test_keyboard.py`, `test_media_group.py`, `test_chat_action.py` and `test_formatting.py` pass, with keyword-only call sites.
- Adding a field to `InlineKeyboardButton` in a fixture IR adds it to `button()` with no hand edit.
- Adding a `foo` / `foo_entities` / `foo_parse_mode` triple to a fixture IR method adds `Text.as_foo_kwargs()` with no hand edit.
- Two runs emit byte-identical output.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Hand-maintained signatures | Drift on every bump | D59 |
| `MediaGroupMiddleware` album aggregation | Withdrawn from 4.0 | D116 |
| `UNSET_PARSE_MODE` sentinel | Removed; `Default("parse_mode")` | 11 §1 |

## Validation

```bash
cargo test -p butcher emit_utils
cargo xtask butcher emit && make dev
uv run mypy aiogram
uv run pytest tests/test_utils
cargo xtask butcher check
```

## Workflow notes

- G-11 consumes the mixins and owns the hand-written classes. This task can land first with the mixins unused.

## Notes
