# B-13 — Gate run + go/no-go decision record

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-00](B-00-freeze-gate-spec.md), [B-01](B-01-crate-maturin-skeleton.md), [B-02](B-02-bench-adapter-memory-estimator.md), [B-03](B-03-decode-runtime.md), [B-04](B-04-spike-type-set.md), [B-05](B-05-views-cache-gc-routing-keys.md), [B-06](B-06-value-semantics-native-api.md), [B-07](B-07-bound-views.md), [B-08](B-08-subclassing-register.md), [B-09](B-09-sendmessage-encoder-response.md), [B-10](B-10-ext-helpers-stub-workflow.md), [B-11](B-11-cache-gc-teardown-ft-tests.md), [B-12](B-12-dispatch-harness.md), [A-06](../A-contracts/A-06-record-3x-baselines.md), [A-08](../A-contracts/A-08-model-oracle.md), [B-14](B-14-unions-envelope-batch-decode.md) |
| Blocks | every plan with `Gate-conditional: yes`, at least [C-18](../C-butcher/C-18-rust-type-emitter.md), [C-19](../C-butcher/C-19-rust-forward-compat-emitter.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md), [C-27](../C-butcher/C-27-port-ext-helpers.md), [D-07](../D-client/D-07-rust-encoder-json.md), [D-08](../D-client/D-08-rust-encoder-multipart.md), [D-09](../D-client/D-09-response-decoder.md), [E-09](../E-runtime/E-09-routing-keys-compiled-rejectors.md), [F-11](../F-fsm/F-11-callbackdata-without-pydantic.md), [F-12](../F-fsm/F-12-aiogram-types-in-fsmdata.md), [H-13](../H-testing-observability/H-13-binding-identity-rewrite.md), [I-17](../I-distribution/I-17-model-semantics-rules.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [D-13](../D-client/D-13-raw-bot-call-raw-method.md), [D-17](../D-client/D-17-rust-entity-rendering-kernel.md), [G-06](../G-features/G-06-lazy-text-capture.md) |
| Gate-conditional | no |
| Decisions | D104, D26, D121, PD-03, PD-30, R01, R02, R03, R04 |
| Sources | [README roadmap, B row](../../research/README.md), [01-models.md §5](../../research/01-models.md), [19 D104, D121](../../research/19-review-resolutions.md), [codex-review.md R01, §10](../../research/codex-review.md), [13-aiogram-rust-review.md §5, §7, B25](../../research/13-aiogram-rust-review.md), [08-build-release.md §5](../../research/08-build-release.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone B is the **binding go/no-go** of aiogram 4.0 (D104, D121). If the spike passes, Rust-native types become
the model layer and the gate-conditional plans proceed. If it fails, the model layer is redesigned from scratch:
there is no pre-committed fallback. Thresholds are never relaxed after a failed run (codex §10). This task runs the
frozen spec (B-00), judges it and records the decision.

## Scope

**In:**
- The full B-02 run of every workload in `benchmarks/b_gate/gate.toml`:
  - Linux x86_64 with uvloop, and macOS arm64;
  - release build (`make bench`), pyo3 ≥0.30, warm protocol;
  - the interpreters chosen in B-00;
  - against the frozen optimised-3.x baseline JSON.
- Semantic results from B-07 and B-11 (named test ids) on cp311 and cp314t.
- Informational developer / release cost (codex §10, 13 §7):
  - cold and incremental release / debug build, `.so` size, import time / RSS of `aiogram._core`;
  - per-unit object sizes via `-C save-temps` (first calibration point for the B25 guard, I-06);
  - the B-10 helper-edit rebuild numbers.
- Recording of everything below.

**Out:**
- Changing thresholds (only by a new owner decision recorded **before** a re-run).
- Editing `v4/research/` (A-02 or the owner folds the result in).
- Implementing the redesign after a no-go (re-planned separately).

## Checklist

- [ ] Confirm that every gated workload in `gate.toml` reports a result (none `missing`) and every gate test id
  exists.
- [ ] Run the full set on Linux and macOS; store raw samples and run records under
  `benchmarks/results/b-gate-<date>-<host>.json` (A-05 results directory).
- [ ] Write `benchmarks/b_gate/RESULT.md`:
  - one row per gated item, with the threshold, measured ratio, absolute µs / bytes (both sides), p5 / p95 and
    pass / fail;
  - the informational table;
  - the list of B-04 opaque fields;
  - every "Decide" choice made in B-00..B-12, copied from their Notes, with owner sign-off status.
- [ ] Verdict **GO** only if every gated item passes on every gated platform and interpreter; otherwise **NO-GO**.
  No partial go.
- [ ] Write a proposed decision entry for the owner (next free D-number), to be added to
  `v4/research/README.md` by the owner or an A-02 follow-up: verdict, date, result link, the conditional decisions it
  confirms or reopens.
- [ ] **On GO:**
  - Gate-conditional plans stay `todo` and become ready.
  - Record the measured hot-field set and layout choices that C-18 must reproduce (PD-30 golden diff).
  - Flag to their owners any B decisions that changed a contract other plans assume (seeding rule, pickle of bound
    objects, `RoutingKeys` fields).
- [ ] **On NO-GO:**
  - Set `Status: blocked` with a Notes link to `RESULT.md` in every gate-conditional plan.
  - Revert the spike directories (PD-03): `crates/aiogram-core/src/generated/`, `crates/aiogram-core/src/types/`,
    the decode / view / encoder modules from B-03..B-09 and B-14, and `tests/test_core/` except the B-01 build tests.
  - Keep the B-01 skeleton, the B-02 harness, `gate.toml`, `RESULT.md` and raw results until the owner re-confirms
    D1 / D6 / D17 (below).
- [ ] Record the **void list** (below) in `RESULT.md` with a per-item status: confirmed (GO) or reopened (NO-GO).
- [ ] On NO-GO, ask the owner to **re-confirm or withdraw D1 (mandatory Rust core), D6 (butcher in Rust) and D17
  (single maturin distribution)**. These are not in D104's conditional list, but they stand or fall by that
  re-confirmation. Record the answer in Notes.
- [ ] No changelog or registry entry (decision record only).

### Void list (reopened on NO-GO, confirmed on GO)

- **D104's conditional set:** D4, D11, D14, D53 (mechanism), D83, D84, D85, D86, D87, D91, D92, D93, D94, D95,
  D102, D103.
- **Also dependent on Rust-native types**, though not in D104's list:
  - D105 (unknown fields as attributes);
  - D106 (cached tuples);
  - D107 (mechanism: nearest decoded union absorbs malformed data);
  - D108 (raw / value semantics);
  - D109 (reserved native names; the overlay rename rule itself survives);
  - D16 (thin re-exports from `_core`);
  - D26 (this gate; a redesign gets its own gate);
  - D99 (unknown kwargs on Rust method classes);
  - D25 / D117 / PD-07 (lazy text stored on frozen Rust fields, rendered by the Rust encoder);
  - D96's rationale (generated method classes not subclassable);
  - PD-15 (entity kernel in Rust: reopen placement);
  - PD-30 and C-18's golden-diff duty.
- **Research mechanisms:** 02 §5.1 (`*_ext.rs` + `.pyi` fragment workflow, Rust type / method emitters) and 08 §7
  items 11–16 (placement rules).
- **README breaking changes** that rest on the model layer: 1 (not pydantic, native API), 2 (all immutable, D15 as
  realised), 3 (subclass `register`), 12 (CallbackData without pydantic, D14), 18 (`model_dump_json` wire names),
  19 (JSON-shaped extras), 22 (`as_` new view), 23 (tuples).
- **Plans:** every plan whose *Gate-conditional* field is `yes` or `partial` (see the plans/README.md index), not just
  this plan's *Blocks* row; on NO-GO each `partial` plan re-plans only its gate-dependent part.
- **Owner re-confirmation required (not voided automatically):** D1, D6, D17.

## Acceptance criteria

The verdict is GO only if **all** of the following hold. These are the README B-row thresholds, as frozen in
`gate.toml` by B-00. Conditions: warm, on pyo3 ≥0.30, Linux + macOS, against optimised 3.x (the A-06 tag), with
absolute µs reported next to every ratio.

- **Parse ≥3×** on the `getUpdates` batch + `sendMessage` response paths (B24) and the other gated decode workloads,
  scoped per B-00.
- **Memory ≥4×**, including accessed trees and a child retained from a batch (R04), with the estimator from B-00.
- **First access ≤2×.**
- **Warm access ≤1.6×** (D26).
- **End-to-end dispatch no slower** than optimised 3.x (B-12 workload, B-00 definition of "no slower").
- **Cache/GC/teardown tests pass** (B-11): concurrent first access returns one wrapper, callback re-entry can't
  deadlock, cycles through Bot / session are collectable, teardown works on 3.11 and free-threaded builds.
- **Two bots can't redirect each other's shortcuts** (R02, B-07).

Any failure → **NO-GO → redesign the model layer** (D104). Recording obligations:
- `RESULT.md` exists with every gated row, raw samples and run records (commits, lock and fixture hashes, toolchain,
  flags, hardware).
- The proposed decision entry and the void-list status table are written.
- On NO-GO, every gate-conditional plan is `blocked` and the spike directories are reverted.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Relaxing a threshold after a failed run | Reconsider the design instead | codex §10, R01 |
| A pre-committed fallback (pydantic + Rust codecs) | No fallback; redesign | D104 |
| A partial go (some workloads pass) | The gate is binding as a whole | D104, README B row |
| Treating D1 / D6 / D17 as automatically void on a no-go | Not in D104's list; the owner re-confirms them | D104 |
| Gating on build time / binary size | 12 types don't extrapolate to ≈665 classes; recorded, judged by I-06 | 13 §7, R25 |

## Validation

```bash
make bench
uv run python -m benchmarks run --cases all --out benchmarks/results/b-gate-4x-linux.json
uv run python -m benchmarks report benchmarks/results/3.x-optimised-linux.json benchmarks/results/b-gate-4x-linux.json   # judged against benchmarks/b_gate/gate.toml; summary written to benchmarks/b_gate/RESULT.md
uv run pytest tests/test_core
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_core
cargo test --workspace
make lint
```

## Workflow notes

- Inputs: everything from B-00..B-12; the frozen baseline JSON (B-02).
- Outputs:
  - the verdict, which the orchestrator reads, since gate-conditional plans need B-13 `done` with GO;
  - `RESULT.md` and raw data;
  - the proposed decision entry;
  - the B25 calibration sample for I-06;
  - hot-field and layout notes for C-18.
- Must run on the A-05 reference hosts; not in CI.

## Notes

- Coordinator default (reconciliation, K12): the void list covers every `yes` or `partial` plan from the plans/README.md
  index, not only this plan's *Blocks*.
