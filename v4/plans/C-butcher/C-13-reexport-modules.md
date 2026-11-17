# C-13 — Per-type / per-method re-export modules and `__init__` (D16)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-09](C-09-resolution-passes.md) |
| Blocks | [C-14](C-14-pyi-stub-emitter.md), [C-23](C-23-check-offline-determinism.md), [H-12](../H-testing-observability/H-12-toolkit-model-api-migration.md), [I-07](../I-distribution/I-07-dependencies-extras-restructure.md) |
| Gate-conditional | partial (D16 is not in D104's list, but B-13's void list reopens D16 on a no-go; see Notes) |
| Decisions | D16, D17, PD-03 |
| Sources | [02-butcher.md §5.2](../../research/02-butcher.md), [08-build-release.md §2](../../research/08-build-release.md), [plans README PD-03](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D16 keeps the 3.x layout: one module per type and per method, so deep imports such as
`from aiogram.types.message import Message` keep working. Each module is a one-line re-export from `aiogram._core`.
`aiogram/types/__init__.py` and `aiogram/methods/__init__.py` import straight from `_core`, so startup reads no
per-type files. A single merged module was rejected (02 §5.2).

## Scope

**In:** `crates/butcher/src/emit/python.rs`:
- `aiogram/types/<snake>.py` and `aiogram/methods/<snake>.py`: `from aiogram._core import X as X` plus `__all__`.
  Module names match 3.x (`message.py`, `send_message.py`), including D18-merged twins (no module for the 7 schema-only
  `Input*`) and D109 renames (field names only, no module change).
- `aiogram/types/__init__.py` and `aiogram/methods/__init__.py`: one `from aiogram._core import (...)` block, sorted, plus `__all__`.
- `aiogram/types/__init__.pyi` / `aiogram/methods/__init__.pyi`: `from .message import Message as Message` re-exports.
- Hand-written Python types (`InputFile` family in `aiogram/types/input_file.py`, `aiogram/types/custom.py` replaced by
  the Rust datetime) are never overwritten. The emitter keeps an allow-list of hand-written modules and fails if the IR
  would emit over one.
- **PD-03:** until B-13 is a *go*, these files are emitted into a staging tree (`target/butcher/emit/aiogram/…`), not
  into `aiogram/`. Switching the output root is a one-line config in `butcher/emit.toml`.

**Out:** stubs (C-14), `module = "aiogram.types"` on pyclasses (C-18), docs import order (C-22).

## Checklist

- [ ] Re-export module emitter with the 3.x naming rule (verify against today's `aiogram/types/*.py` names: 0 renamed modules except the removed and merged ones).
- [ ] `__init__.py` / `__init__.pyi` emitters.
- [ ] Hand-written module allow-list and the overwrite guard.
- [ ] Output-root switch (staging vs `aiogram/`).
- [ ] Test: the set of emitted module names equals the 3.x `aiogram/types` + `aiogram/methods` module set minus the ledger-reset types (`KeyboardButtonRequestUser`, `UserShared`, `StoryAreaPosition`, per 11 §1) and minus hand-written modules such as `base.py`, `custom.py`, `input_file.py` and `downloadable.py`. A module added upstream since 10.4 is listed explicitly in the test.
- [ ] Migration-registry entry (PD-13): none new; module paths are unchanged except removed types (covered by C-26 inventory).
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `import aiogram.types` on a dev build opens no `aiogram/types/<x>.py` file (`python -X importtime` shows only `aiogram.types` and `aiogram._core`).
- `from aiogram.types.message import Message` and `from aiogram.types import Message` give the same object.
- The module-set diff test passes.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Single merged module | Breaks deep imports; ≈1.5 MB stub growing past PyCharm's 2.5 MB limit; unreviewable diffs | D16 |
| `__init__` importing through submodules | Startup would read 600+ files | D16 |
| Writing into `aiogram/` before the gate | Spike stays unwired | PD-03 |

## Validation

```bash
cargo test -p butcher emit_python
cargo xtask butcher emit && make dev
uv run python -X importtime -c "import aiogram.types" 2>&1 | grep -c "aiogram.types\."
uv run pytest tests
cargo xtask butcher check
```

## Workflow notes

- C-14 writes the stubs beside these modules. B-13's go flips the output root.

## Notes

- D16 isn't on D104's conditional list, but these re-exports presume `_core` exposes one class per type. If B-13 is a
  no-go, revisit this file together with the model-layer redesign.

- Coordinator default (reconciliation, K11): Gate-conditional set to `partial`, because B-13's void list reopens D16.
