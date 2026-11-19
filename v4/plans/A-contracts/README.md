# Story A — Contracts & baselines

**Branch:**
- `dev-3.x` for the corpus, bench, oracles and registry. They are merged forward to `dev-4.x` (PD-12).
- A-01 also creates `dev-4.x`.

**Goal:** before any optimisation, there exist:
- (1) a pinned corpus with hashes;
- (2) a benchmark harness using the gate's method;
- (3) a behaviour oracle: an **external pinned 3.x venv** (PD-12) with model, request/response and routing
  differential harnesses, difference manifests and poison control (R26);
- (4) recorded stock and "optimised 3.x" baselines;
- (5) research pages that state 19 + PD-01..PD-31 directly;
- (6) the single migration registry (PD-13).

**Exit gate (README D121):**
- oracle + pinned benchmarks exist before any optimisation;
- concretely: A-04, A-05, A-07, A-08, A-09 and A-10 are `done` before any 3x performance PR merges and before B-03
  starts, and A-06 is `done` before B-00 freezes the gate.

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [A-01](A-01-bootstrap-dev-4x.md) | Bootstrap `dev-4.x`, commit `v4/`, sync policy | — | no | S |
| [A-02](A-02-apply-resolutions.md) | Apply 19 + PD-01..PD-31 to research pages | A-01 | no | M |
| [A-03](A-03-poison-update-decision.md) | 3.x poison-update decision record (owner sign-off) | — | no | S |
| [A-04](A-04-pinned-corpus.md) | Pinned corpus + manifest | — | no | M |
| [A-05](A-05-bench-harness.md) | Benchmark harness + method | A-04 | no | M |
| [A-06](A-06-record-3x-baselines.md) | Record stock + optimised 3.x baselines | 3x-01, 3x-03, 3x-07, 3x-08, 3x-09, 3x-11, 3x-12, 3x-14, A-04, A-05 | no | S |
| [A-07](A-07-differential-framework.md) | Differential framework (venvs, manifests, poison) | A-04 | no | M |
| [A-08](A-08-model-oracle.md) | Model oracle, 3.x side | A-04, A-07 | no | M |
| [A-09](A-09-request-oracle.md) | Request/response oracle, 3.x side | A-04, A-07 | no | M |
| [A-10](A-10-routing-oracle.md) | Routing oracle, 3.x side | A-04, A-07 | no | L |
| [A-11](A-11-migration-registry.md) | Migration registry schema, ids, seed | A-01 | no | M |

## Recommended order and lanes

1. **Start immediately, in parallel:** A-01 (embargo check first), A-03 (send to the owner), A-04.
2. **After A-04:** A-05 and A-07 in parallel.
3. **After A-07:** A-08, A-09 and A-10 in parallel. A-10 is the longest.
4. **After A-01:** A-02 and A-11. A-11 unblocks the 3x migration-baseline lane.
5. **After the baseline-relevant 3x quick wins merge:** A-06. It unblocks B-00 / B-13.

Owner sign-offs requested by this story:
- A-03 Q1–Q10;
- A-01 embargo and publishing of the core-dev brief;
- A-05 tool choice;
- A-11 id blocks and authority rule.
