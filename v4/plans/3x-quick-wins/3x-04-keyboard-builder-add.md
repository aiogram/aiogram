# 3x-04 — `KeyboardBuilder`: fix the O(n²) `add()`, cheaper isolated `export()`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | D120 (reworked #2), R27 |
| Sources | [09 #2](../../research/09-3x-quick-wins.md), [06 §1](../../research/06-utils.md), [codex-review R27 / §11](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`KeyboardBuilder.add()` (`aiogram/utils/keyboard.py`) calls `self.export()`, which does a `deepcopy(self._markup)`.
Every added button copies the whole markup again, so building is O(n²): 30 buttons take 4.4 ms and 100 buttons take
46 ms (README).

The original idea was a shallow `export()`. R27 showed that premise was wrong: the buttons are
`MutableTelegramObject`s, and the current `export()` keeps exported objects isolated from the builder (a codex §11
probe). D120 reworks the item:
- fix `add()` so it no longer exports;
- make `export()` use a per-button `model_copy`, which keeps the isolation: 63 → 8.7 µs.

## Scope

**In:**
- `add()` mutates `self._markup` in place instead of going through `export()`. The validation order and errors stay
  the same.
- `export()` returns new row lists with a `model_copy()` of each button. Measure `model_copy(deep=True)` against the
  shallow copy and choose the cheapest one that passes the isolation tests, then record the choice.
- Check every other internal caller of `export()` (`row`, `adjust`, `as_markup`, `attach`, `copy`, `from_markup`).
  Each must keep its current isolation guarantee.

**Out:** making buttons immutable (D15, 4.0 only).

## Checklist

- [ ] Baseline with A-05 on `keyboard.inline.30` and `keyboard.inline.100` (build + `as_markup`).
- [ ] Rewrite `add()` without `export()`.
- [ ] `export()` with per-button copies. Decide between `model_copy()` and `model_copy(deep=True)` with the tests
      below, and record the result in Notes.
- [ ] Isolation tests (they exist only as probes today):
  - mutating `button.text` on an exported button doesn't change the builder;
  - mutating a builder button after export doesn't change the export;
  - nested `callback_game` / `web_app` objects are isolated.
- [ ] Tests for `add()` row filling at `max_width` edge cases.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.bugfix.rst`: "`KeyboardBuilder.add()` is no longer quadratic in the number
      of buttons".
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-05 `compare` on `keyboard.inline.100`: median ≥ 10× faster than the parent commit.
- `export()` keeps object isolation (the tests above), and every existing `tests/test_utils/test_keyboard.py` case
  passes unchanged.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Shallow `export()` (original 09 #2) | Breaks exported-object isolation for `MutableTelegramObject` buttons | R27, D120 |
| Keep `deepcopy` of the whole markup | O(n²) | 09 #2 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases keyboard.inline.30,keyboard.inline.100
```

## Workflow notes

Independent of everything else. Not part of the gate baseline (A-06 records it for G-11 / G-10 reference only).

## Notes
