# H-11 — Generated toolkit tables + fake-coverage guard

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-10](H-10-testing-world-import.md), [C-01](../C-butcher/C-01-crate-xtask-ir-snapshot.md), [C-08](../C-butcher/C-08-merge-cross-check.md), [C-16](../C-butcher/C-16-router-observers-update-tables.md), [D-13](../D-client/D-13-raw-bot-call-raw-method.md) |
| Blocks | [H-12](H-12-toolkit-model-api-migration.md) |
| Gate-conditional | no |
| Decisions | D95, D6, D118, R26, D12–D15 (`ContentType` removed) |
| Sources | [14-testing.md §3 "Generated from the IR"](../../research/14-testing.md), [01-models.md §3.7 introspection row](../../research/01-models.md), [02-butcher.md §3](../../research/02-butcher.md), [19 D118, R26](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The toolkit discovers API shape at runtime through pydantic: `model_fields` (34 uses), `__returning__`,
`ContentType` (24 uses). In 4.0 there is no public field introspection (D95), `ContentType` is removed, and 01
§3.7 says the toolkit uses **tables generated from the IR**.

14 §3 also wants fake coverage to keep up with each Bot API release. The planning resolution enforces that with a
**pytest guard**, not butcher `check`. Butcher is Rust and can't see the Python `@models` registry.

## Scope

**In:**
- A butcher emitter (C framework) writing `aiogram/test/_tables.py`. The file is committed and covered by
  `cargo xtask butcher check` like every emitted file. It holds:

  | Table | Content | Replaces |
  |---|---|---|
  | `RETURNS` | method name → wire return type, including `True`/union shapes | `__returning__` introspection in `synthesis.py` |
  | `FIELDS` | type name → ordered `(wire_name, python_name, type_ref, required)` | `model_fields` uses |
  | `MEDIA_FIELDS` | send/edit method → its primary media parameter (the `InputFile`-typed field) | `modeling.MEDIA_FIELDS` |
  | `POSTED_CONTENT` | the message-content kinds | `ContentType` in `modeling.content_kind` |

  `FIELDS` uses the IR's direction-specific requiredness (D118), and the request-side shape for `Input*` merged
  twins (D18). `POSTED_CONTENT` **reuses** C-16's routing content-kind table rather than emitting a second one.
  Update-type coverage reuses C-16's update table.
- **Fake-coverage guard** (pytest, in `tests/test_testing/`):
  - every IR method in `RETURNS` is either registered with `@models` (`modeling.models`) or listed in an explicit
    `SYNTHESIZED` set in `aiogram/test/synthesis.py`;
  - every update type in C-16's table has a trigger in `actors.py` or an explicit `NO_TRIGGER` entry;
  - the failure message names the missing items and the two ways to resolve them.
- Default-field resolution is **not** generated here. The fake reuses D-10's resolve/render step (H-12).

**Out:**
- Switching the toolkit's code to these tables (H-12).
- `BOT_RIGHTS` semantics (see the Decide item).
- Rejection texts (H-17).

## Checklist

- [ ] Emitter module in the butcher crate. Output path and header follow C conventions. Deterministic ordering.
- [ ] Register the output with `butcher check`.
- [ ] Pytest guard for methods and update types, including a negative test that injects a fake IR method and sees
      the guard fail.
- [ ] **Decide `BOT_RIGHTS`.** Admin rights per method are not in the IR (proposed default: it stays hand-written
      in `modeling.py`; the guard also requires every method with a `chat_id` parameter to be in `BOT_RIGHTS` or in
      an explicit `NO_RIGHTS_NEEDED` set). Record the decision in *Notes* and flag it to the owner.
- [ ] Unit tests of the emitter (snapshot of a small IR fixture) in `cargo test`.
- [ ] No changelog (internal), unless the owner wants the guard documented for contributors (then add it to
      CONTRIBUTING).

## Acceptance criteria

- `cargo xtask butcher check` passes with `_tables.py` committed, and fails when it is edited by hand.
- Adding a method to the IR without a fake model or `SYNTHESIZED` entry makes the pytest guard fail with a message
  naming the method.
- `_tables.py` is byte-identical across two emitter runs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Butcher `check` failing on missing fake models (14 §3) | Butcher (Rust) can't import the Python `@models` registry; a pytest guard gives the same effect with no Rust coupling | planning resolution |
| Runtime introspection (`model_fields`) | Removed in 4.0 | D95 |
| A generated Default resolver for the fake | A second implementation of the encoder's contract, the R26 "same IR on both sides" blind spot; reuse D-10 | planning resolution, R26 |
| A separate posted-content table | C-16 already emits content kinds for routing | — |

## Validation

```bash
cargo fmt --check
cargo clippy -- -D warnings
cargo test
cargo xtask butcher check
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs:
  - C-01: crate, xtask, IR format;
  - C-08: merged IR;
  - C-16: update and content-kind tables.
- Output: `_tables.py`, consumed by H-12. The guard keeps the fake current on every Bot API bump, so add it to the
  bump checklist (I-08 contributor workflow).
- C-06 has no "fake marks" overlay kind (dropped in reconciliation); this pytest guard is the only fake-coverage
  check, and C-23 has no rule for it.

## Notes
