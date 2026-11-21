# I-06 — Largest-codegen-unit guard (B25)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-05](I-05-pr-ci-structure-caching-coverage.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md) |
| Blocks | — |
| Gate-conditional | yes (D102 one-crate layout) |
| Decisions | D102, 13 B18, 13 B25, R25 |
| Sources | [08-build-release.md §5, §7.12–16](../../research/08-build-release.md), [13-aiogram-rust-review.md B18, B25](../../research/13-aiogram-rust-review.md), [19 R25](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D102 puts the whole core in one crate with codegen-unit-aware placement rules (08 §7.13–16). In aiogram_rust the build
cost came from code that **landed** in one or two units, not from total code size. Total IR −15% bought almost nothing.

R25 clarifies that the placement rule is the current rustc heuristic, not a language guarantee. A guard on the largest
unit verifies it, with a threshold calibrated on real CI hardware. Calibration only means something on the full
generated crate (C-18 types, C-20 methods), not on the 12 spike types.

## Scope

**In:**
- A scheduled (weekly + `workflow_dispatch`) job: release build with `-C save-temps`. It records per-unit object sizes
  and the cold-build wall-clock, and compares them with a committed baseline (`ci/codegen-baseline.json`).
- Fail when the largest unit exceeds **2× the median** (08 §5) or the cold build regresses by more than **15%**. Both
  thresholds are kept in the baseline file so recalibration is one reviewed diff.
- A separate **nightly-toolchain** job with `-Ztime-passes`, so the compiler being compared never changes (R25). It
  reports and never fails.
- A `cargo llvm-lines` report artifact (08 §7.12) for diagnosis.

**Out:**
- Fixing placement regressions (the owning C/D plan fixes them).
- PR-time build-time gating.

## Checklist

- [ ] Script `ci/codegen_units.py`: parse `target/release/deps/*.o` sizes for the `aiogram_core` crate, emit JSON
      (max, median, ratio, wall-clock).
- [ ] Calibrate: run the job 5× on the CI runner class. Store the medians as the baseline. Record the spread in Notes.
- [ ] **Check the 2× threshold against the real distribution** (R25: an inherently skewed but healthy build can trip
      it). If the calibrated healthy ratio is already above 2×, propose a threshold from the data, record it in Notes
      and flag it to the owner rather than silently raising it.
- [ ] Nightly `-Ztime-passes` job with a pinned nightly date in the workflow.
- [ ] The scheduled failure opens an issue (same mechanism as I-02's dry run).
- [ ] Tests for the parser script (fixture directory with fake `.o` sizes), 100% coverage.
- [ ] No changelog fragment (`skip news`).

## Acceptance criteria

- On the calibrated baseline the guard passes 5 of 5 runs.
- A scratch commit adding a generic `fn f<T>` per-class body (the anti-pattern in 08 §7.13) that inflates one unit
  makes the guard fail.
- The baseline file contains the thresholds, runner class and toolchain version.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Guarding total code size / IR lines | Total code is not the signal | 13 B25 |
| Same toolchain for `-Ztime-passes` | Needs nightly; must not change the compiler being compared | R25 |
| Three-crate split | One crate with placement rules was faster and smaller | D102 |

## Validation

```bash
cargo build --release && python ci/codegen_units.py target/release
uv run pytest tests/ci -q
make lint-workflows
```

## Workflow notes

- Inputs: C-18 / C-20 (full crate), I-05 (cache and workflow conventions).
- If B-13 is a no-go, this plan is `blocked` with D102.

## Notes

(empty)
