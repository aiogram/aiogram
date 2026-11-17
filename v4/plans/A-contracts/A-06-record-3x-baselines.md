# A-06 — Record the 3.x baselines (stock + "optimised 3.x" tag)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (tag + results file, merged forward to `dev-4.x`) |
| Depends on | [A-04](A-04-pinned-corpus.md), [A-05](A-05-bench-harness.md), [3x-01](../3x-quick-wins/3x-01-polling-poison-isolation.md), [3x-03](../3x-quick-wins/3x-03-magicfilter-inline.md), [3x-07](../3x-quick-wins/3x-07-drop-model-rebuild-loop.md), [3x-08](../3x-quick-wins/3x-08-butcher-literal-tags.md), [3x-09](../3x-quick-wins/3x-09-json-request-body.md), [3x-11](../3x-quick-wins/3x-11-prebuilt-middleware-chains.md), [3x-12](../3x-quick-wins/3x-12-small-dispatch-costs.md), [3x-14](../3x-quick-wins/3x-14-callback-data-prefix-fast-fail.md) |
| Blocks | [B-00](../B-spike/B-00-freeze-gate-spec.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [B-02](../B-spike/B-02-bench-adapter-memory-estimator.md), [B-12](../B-spike/B-12-dispatch-harness.md), [E-21](../E-runtime/E-21-e-exit-gate.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md) |
| Gate-conditional | no |
| Decisions | D104, D26, PD-12, codex-review §10 ("do not use an unimplemented 3.x optimisation as the measured baseline") |
| Sources | [README milestone B](../../research/README.md), [01 §2, §5](../../research/01-models.md), [13 §1](../../research/13-aiogram-rust-review.md), [codex-review §10](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The B gate (parse ≥ 3×, memory ≥ 4×, first access ≤ 2×, warm access ≤ 1.6×, end-to-end dispatch no slower) is
measured "vs optimised 3.x". That baseline must be **real merged code**, measured with the gate's method on the
gate's inputs. 13 §1 showed the baseline keeps moving: pydantic 2.14 alone took 41 → 25 µs. Only a tagged commit and
a committed results file make the gate reproducible.

## Scope

**In:**
- **Stock 3.x:** results for the current 3.x release (3.32.0 at planning time; use the latest release when this
  runs) on all A-04 cases.
- **Optimised 3.x:**
  - tag `v4-baseline/3.x-optimised` on the `dev-3.x` commit where the baseline-relevant quick wins have merged:
    3x-01, 03, 07, 08, 09, 11, 12, 14;
  - 3x-04, 05, 06, 13 and 17 are included if merged, and listed either way;
  - results on all A-04 cases.
- Both runs on **Linux x86_64 with uvloop** and on **macOS arm64**, using the A-05 method. Optionally a low-core
  Linux runner (README "Where help is most useful").
- Commit `benchmarks/results/3.x-stock-<os>.json` and `benchmarks/results/3.x-optimised-<os>.json`, plus a short
  `benchmarks/results/README.md` table: per gate metric, the stock vs optimised medians and the ratio, plus absolute
  µs and KB.

**Out:**
- The 4.0 measurements and the gate decision: B-13.
- Re-running for later 3.x releases: optional, under a new label.

## Checklist

- [ ] Confirm the dependencies have merged; list any missing ones and wait for them.
- [ ] Create the tag and push it.
- [ ] Run A-05 `run --cases all` for stock and optimised, on both OSes (and the low-core runner if available).
      Record the machine details automatically, as A-05 does.
- [ ] Check that noise is under control: the `HEAD` vs `HEAD` calibration from A-05 stays within ±3% on each machine.
- [ ] Commit the results and the summary table.
- [ ] Compare with the README estimates (for example "≈1.7× parse, ≈5× import est.") and note large deviations in
      Notes. Don't edit the research pages; A-02 can reference this file.
- [ ] Changelog: none. Use the `skip news` label.

## Acceptance criteria

- The tag `v4-baseline/3.x-optimised` exists, and its commit contains every listed quick win (`git log` check).
- Four results files exist (2 baselines × 2 OSes), each with raw samples for every gate input: `update.realistic`,
  `update.text.small`, `response.getUpdates.100`, `response.sendMessage`, the memory cases, `routing.52-handlers`
  and `routing.5routers-30handlers`.
- The summary table has absolute numbers and ratios for each gate metric.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Gate against stock 3.x | Inflates every ratio | 01 §2, 09 intro |
| Gate against projected / unmerged optimisations | Not a measured baseline | codex-review §10, R27 |
| Gate on README numbers | Different estimator and payloads | codex-review §10 |

## Validation

```bash
git tag -l 'v4-baseline/*'
uv run python -m benchmarks report benchmarks/results/3.x-stock-linux.json benchmarks/results/3.x-optimised-linux.json
```

## Workflow notes

- **Outputs:** the tag and results files are the "optimised 3.x" for B-00 (freezing the gate spec) and B-13 (the
  gate run).
- If more 3.x optimisations land later, B-13 uses the baseline that B-00 froze; a new baseline needs a new label
  and an owner decision.

## Notes
