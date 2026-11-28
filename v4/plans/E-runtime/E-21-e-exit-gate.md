# E-21 — Milestone E exit gate: routing differential, benchmarks, lifecycle and multi-Runner matrices

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-01](E-01-dispatcher-filter-removals.md), [E-02](E-02-dispatch-table-executor.md), [E-03](E-03-snapshot-lifecycle.md), [E-04](E-04-router-graph-multi-parent-flags.md), [E-05](E-05-typed-observers-unknown-update.md), [E-06](E-06-middleware-api.md), [E-07](E-07-sync-filter-execution.md), [E-08](E-08-magic-filter-compile.md), [E-09](E-09-routing-keys-compiled-rejectors.md), [E-10](E-10-flag-spec.md), [E-11](E-11-error-model-bubbling.md), [E-12](E-12-runtime-errors.md), [E-13](E-13-runner-lifecycle-bot-registry.md), [E-14](E-14-feed-paths-forward-compat-dispatch.md), [E-15](E-15-poller.md), [E-16](E-16-webhook-core-aiohttp-sources.md), [E-17](E-17-asgi-app.md), [E-18](E-18-compat-wrappers.md), [E-19](E-19-multi-runner-free-threading-sharding.md), [E-20](E-20-typed-di-typeddicts.md), [A-05](../A-contracts/A-05-bench-harness.md), [A-06](../A-contracts/A-06-record-3x-baselines.md), [A-10](../A-contracts/A-10-routing-oracle.md), [A-07](../A-contracts/A-07-differential-framework.md), [E-22](E-22-single-bot-sharding.md), [E-23](E-23-bot-registry.md) |
| Blocks | [J-01](../J-ga/J-01-feature-inventory-audit.md), [H-20](../H-testing-observability/H-20-integration-layer-exit-gate.md), [I-20](../I-distribution/I-20-examples-port-smoke.md), [I-23](../I-distribution/I-23-beta-pre-release.md) |
| Gate-conditional | partial — the routing benchmark thresholds depend on E-09 (B-05 `routing_keys()`) |
| Decisions | D121 (milestone E exit), D111, D48, D34, PD-12, PD-19, README breaking changes 13, 16, 17, 24 |
| Sources | [README roadmap E](../../research/README.md), [codex-review §9, §10](../../research/codex-review.md), [03-routing.md §2–§3](../../research/03-routing.md), [12-runtime.md](../../research/12-runtime.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

README milestone E: "routing differences match the decisions; lifecycle fault injection; multi-Runner tests". Each E
plan has its own tests; this plan runs them together against the external 3.x oracle (PD-12) and the pinned
benchmarks, and records the result so milestones F/G/H build on a verified boundary.

## Scope

**In:**
- Full A-10 routing differential (A-07 harness, pinned 3.x venv) against the 4.0 executor with rejectors on; every
  mismatch is either covered by a difference-manifest entry with a decision id (D111, breaking 13, D48, D34, D12,
  D42) and a narrow assertion, or a bug.
- Benchmarks on Linux and macOS (A-05 harness, A-06 optimised-3.x baseline): the E-02, E-07, E-09 thresholds;
  results file committed next to the baselines.
- Lifecycle fault-injection matrix (E-13), registry fault-injection matrix (E-23), webhook matrix (E-16/E-17), poller matrix (E-15), sharding/free-threading
  matrix (E-19) and the sharding matrix (E-22) run as one CI workflow job set.
- Audit that every "Decide X" item in E-02…E-20 has a recorded decision (owner or default) in its plan's Notes; any
  open one is listed here as a blocker.
- Audit that every user-visible E break has a registry entry (PD-13) and a changelog fragment.

**Out:**
- New features or fixes (open them as separate plans or reopen the owning plan).

## Checklist

- [ ] Differential run; manifest reviewed; zero unexplained mismatches.
- [ ] Benchmarks run, thresholds met or a Notes entry with numbers and a decision request.
- [ ] Fault-injection / webhook / poller / sharding matrices green on CPython 3.11–3.15 and 3.14t.
- [ ] "Decide" audit and registry/changelog audit.
- [ ] Milestone record in this plan's Notes (date, commit, numbers, open items).

## Acceptance criteria

- Differential: 0 mismatches outside the manifest.
- Bench (A-04 case `routing.52-handlers`, the 03 §2 scenario): worst case ≤ 90 µs, fixed ≤ 15 µs;
  `routing.100-commands` unmatched ≤ 25 µs; end-to-end dispatch on `routing.5routers-30handlers` (the B-12 realistic
  router) no slower than optimised 3.x.
- All matrices green; no task or session leaks reported by the leak checks.
- No open "Decide" item without a recorded outcome.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| In-tree 3.x reference path for the differential | Oracle is the external pinned venv | PD-12 |
| Gate on ratios only | Baseline keeps moving; absolute µs required | 13 §1, codex §10 |

## Validation

```bash
make dev
uv run pytest tests -q
uv run python -m differential run --kind routing --left pypi:aiogram==<A-10 pinned 3.x version> --right path:.
PYTHON_GIL=0 uv run --python 3.14t pytest tests -q
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases routing.52-handlers,routing.100-commands,routing.5routers-30handlers
make lint
uv run mypy aiogram
```

## Workflow notes

- Inputs: every E plan, A-05/A-06/A-10. Output: the E milestone record consumed by J-01 (feature inventory) and by
  F/G/H plans that need a stable routing/runtime boundary.

## Notes
