# G-11 — Generated utils signatures, immutable-output builders

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [C-17](../C-butcher/C-17-utility-signature-emitter.md), [C-14](../C-butcher/C-14-pyi-stub-emitter.md), [G-08](G-08-formatting-on-kernel.md), [G-10](G-10-utils-removals.md) |
| Blocks | [I-18](../I-distribution/I-18-positional-to-keyword-rule.md) |
| Gate-conditional | no (signatures come from the IR; runtime bodies call the public type constructors) |
| Decisions | 06 §4 "Defaults" (generated signatures, no D-number), D15, D100, PD-02, PD-23, D99 |
| Sources | [06-utils.md §4](../../research/06-utils.md), [11-removals.md §1](../../research/11-removals.md), [02-butcher.md §5](../../research/02-butcher.md), [09-3x-quick-wins.md #2](../../research/09-3x-quick-wins.md), [plans README §1](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Several utils copy Bot API type fields by hand and drift on every Bot API bump (06 §4):
- `InlineKeyboardBuilder.button()`;
- `ReplyKeyboardBuilder.button()`;
- `MediaGroupBuilder.add_*()`;
- `ChatActionSender.<action>()`;
- `Text.as_*_kwargs()`.

In 4.0 their **signatures and docstrings** are generated from the IR by C-17. The bodies stay hand-written and
delegate to the type constructors. Numbering note: the research README groups this under "D59–D62", but D59 is the
withdrawn album middleware (D116). The decision is 06 §4 "Defaults" and has no D-number.

## Scope

**In:**
- Consume C-17's emitter output in `aiogram/utils/keyboard.py`, `media_group.py`, `chat_action.py` and
  `formatting.py`. The structure is C-17's call: a generated mixin or `.pyi` + `**kwargs` body. Record the chosen
  shape in Notes. Requirements:
  - `InlineKeyboardBuilder.button()` / `ReplyKeyboardBuilder.button()` take every field of
    `InlineKeyboardButton` / `KeyboardButton`, keyword-only (D100/PD-02). Stubs have no `**extra` (PD-23); unknown
    kwargs are forwarded at runtime with the D99 one-time warning.
  - `MediaGroupBuilder.add_audio/add_photo/add_video/add_document` and `add(type=…)` mirror `InputMedia*` fields,
    with `parse_mode: str | None = Default("parse_mode")` instead of `UNSET_PARSE_MODE` (11 §1).
  - `ChatActionSender.<action>()` is generated from the `ChatAction` enum, one per member, with the 3.x parameter
    set.
  - `Text.as_*_kwargs()` is generated one per IR triple `X` / `X_entities` / `X_parse_mode`. 3.x hand-writes
    `as_kwargs`, `as_caption_kwargs`, `as_poll_question_kwargs`, `as_poll_explanation_kwargs` and
    `as_gift_text_kwargs`; all of them must still exist. Also add a generic `as_kwargs_for("X")`. The lazy rule from
    G-09 applies: omit siblings when the `Text` is lazy.
- **Builders stay mutable and fluent and produce immutable types** (D15). `export()` / `as_markup()` build the
  immutable markup once. There is no deepcopy, because buttons are immutable (06 §2). 3x-04's O(n²) fix is carried
  over.
- `cargo xtask butcher check` fails when a builder signature is stale.

**Out:**
- The emitter: C-17.
- `force_reply` on `as_markup` is kept (PD-32); not touched here.
- Album aggregation (`MediaGroupMiddleware`): withdrawn (D116).

## Checklist

- [ ] Wire C-17 output into the four modules; delete the hand-copied parameter lists.
- [ ] Generated `MediaGroupBuilder` signatures use `Default("parse_mode")`. D-01 removes the `UNSET_*` sentinels,
      swaps `media_group.py` to `Default("parse_mode")` and owns the registry entry; nothing to remove here.
- [ ] Keep every 3.x method name (`as_caption_kwargs`, …) and argument (`replace_parse_mode=`) of `Text`.
- [ ] Bot API bump rehearsal: add a fake field to a fixture IR and check that `button()` gains it with no hand edit.
- [ ] Benchmarks (A-05 harness): `InlineKeyboardBuilder` with 30 and 100 buttons, `export()` + `as_markup()`. Pinned
      inputs from 06 §2 / 09 #2.
- [ ] **Decide whether `MediaGroupBuilder.add(type=…)`'s positional/keyword shape changes** (3.x `add()` takes
      `type` and `media` as keyword-only; proposed default: unchanged). Record in Notes.
- [ ] Tests (100% coverage of new code); generated-signature snapshot test.
- [ ] Changelog fragment (`feature`; the `UNSET_*` removal fragment is D-01's).

## Acceptance criteria

- `cargo xtask butcher check` passes, and fails after deleting one generated parameter by hand.
- `InlineKeyboardBuilder` 100-button build + `as_markup()` is **no slower than the 3x-04 optimised baseline** that
  A-06 records, and **≤ 1 ms** on the pinned input (3.x stock: 46 ms). If 1 ms proves unrealistic on Rust
  constructors, record the measured value in Notes and flag it.
- `inspect.signature(InlineKeyboardBuilder.button)` lists exactly the `InlineKeyboardButton` fields, all
  keyword-only. mypy rejects an unknown kwarg in a typed test file.
- `Text(...).as_kwargs_for("caption")` equals `as_caption_kwargs()`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping hand-written signatures | Drift on every Bot API bump | 06 §4 |
| Generating the bodies too | Bodies only delegate to constructors | 06 §4 |
| Opt-in album aggregation | Withdrawn; can't work behind the FSM lock | D116 |
| Positional `button(text, …)` | All generated signatures keyword-only | D100, PD-02 |
| `**extra` in stubs | Unknown kwargs are runtime-only | PD-23 |

## Validation

```bash
cargo fmt --check && cargo clippy -- -D warnings && cargo test
cargo xtask butcher check
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: C-17 (emitter + IR triples), C-14 (stub merge), G-08 (formatting on the kernel), G-10 (`force_reply`
  removal in the same files).
- Output: I-18 (positional → keyword codemod) uses the generated signatures.

## Notes
