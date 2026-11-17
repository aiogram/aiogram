# B — Model spike

**Goal.** Prove or refute, with frozen numbers, that Rust-native lazy types (D4) beat optimised 3.x enough to carry
aiogram 4.0. B is the **binding go/no-go** (D104, D121). The spike lives on `dev-4.x` and is **not wired** into
`aiogram.types` (PD-03): the 3.x pydantic package sits untouched beside `aiogram._core`, so both model layers run in
one process. The spike types are **hand-written in emitted shape** (PD-30); C-18 must reproduce them as a golden diff.

**Exit gate** (README B row, frozen by [B-00](B-00-freeze-gate-spec.md), judged by [B-13](B-13-gate-run-and-decision.md)).
Conditions: against optimised 3.x (the A-06 tag), warm on pyo3 ≥0.30, Linux + macOS.
- parse ≥3×, including the `getUpdates` batch + `sendMessage` response paths (B24);
- memory ≥4×, including accessed trees and a child retained from a batch;
- first access ≤2×;
- warm access ≤1.6×;
- end-to-end dispatch no slower;
- cache/GC/teardown tests pass.

**Fail → redesign the model layer.** Gate-conditional plans become `blocked`, and the spike directories are reverted.
D1 / D6 / D17 need owner re-confirmation (void list in B-13).

## Tasks

| ID | Title | Depends on | Gate-conditional | Size |
|---|---|---|---|---|
| [B-00](B-00-freeze-gate-spec.md) | Freeze the gate spec | A-04, A-05, A-06 | no | M |
| [B-01](B-01-crate-maturin-skeleton.md) | Crate + maturin skeleton + minimal CI | A-01 | no | M |
| [B-02](B-02-bench-adapter-memory-estimator.md) | Bench harness 4.0 adapter + memory estimator (extends A-05) | A-04, A-05, A-06, B-00, B-01 | no | M |
| [B-03](B-03-decode-runtime.md) | Decode runtime core: field tables, value kinds, sparse layout | B-01 | no | M |
| [B-04](B-04-spike-type-set.md) | Spike type set (hand-written, emitted shape) | B-00, B-03, B-14 | no | L |
| [B-05](B-05-views-cache-gc-routing-keys.md) | Python views, wrapper cache, GC, `routing_keys()` | B-04 | no | L |
| [B-06](B-06-value-semantics-native-api.md) | Value semantics + native serialization API | B-05 | no | M |
| [B-07](B-07-bound-views.md) | Bound views (D103) | B-05, B-06 | no | S |
| [B-08](B-08-subclassing-register.md) | Subclassing + `register` | B-05, B-06 | no | M |
| [B-09](B-09-sendmessage-encoder-response.md) | `SendMessage` + encoder + response path | B-01, B-04, B-05, B-06, B-07, B-14 | no | L |
| [B-10](B-10-ext-helpers-stub-workflow.md) | `*_ext.rs` helpers + stub workflow | B-01, B-05 | no | M |
| [B-11](B-11-cache-gc-teardown-ft-tests.md) | Cache/GC/teardown/free-threading tests | B-01, B-05, B-06, B-07, B-08, B-09 | no | M |
| [B-12](B-12-dispatch-harness.md) | End-to-end dispatch harness | A-06, A-10, B-00, B-02, B-05, B-07, B-09 | no | M |
| [B-13](B-13-gate-run-and-decision.md) | Gate run + go/no-go record | A-06, A-08, B-00, B-01, B-02, B-03, B-04, B-05, B-06, B-07, B-08, B-09, B-10, B-11, B-12, B-14 | no | M |
| [B-14](B-14-unions-envelope-batch-decode.md) | Decode runtime: unions, depth guard, envelope, `getUpdates` batch | B-03 | no | M |

No B task is gate-conditional: B *is* the gate.

## Order and parallel lanes

```
lane 1 (critical): B-01 ─▶ B-03 ─▶ B-14 ─▶ B-04 ─▶ B-05 ─▶ B-06 ─▶ B-07 ─▶ B-09 ─▶ B-12 ─▶ B-13
lane 2 (measure):  B-00 (after A-04/05/06) ─▶ B-02 (after B-01) ─────────────────▲
lane 3 (after B-05/B-06): B-08, B-10, B-11 ─────────────────────────────────────┘
```

- B-00 and B-01 start together. B-01 is also a prerequisite for C-01, D-07 and I-01 (PD-31), so land it first.
- B-03 (then B-14) and B-02 run in parallel. In B-04, `Message` and the unions can be split between two people.
- After B-05 / B-06: B-07 → B-09 on the critical path; B-08, B-10 and B-11 in parallel.
- Effort is about 40 person-days. The research's "≈3 weeks" holds with about 3 people on the lanes above; one person
  needs about 8 weeks.

## Contracts B hands to other stories

| To | What |
|---|---|
| C | Golden emitted shape for types, unions / `Unknown`, methods (C-18, C-19, C-20); `*_ext.rs` + `.pyi` fragment convention (C-14, C-27); measured hot fields |
| D | Encoder / decoder API, value-writer rules (PD-11), render-hook call-out (D-07..D-10); seed HTML unparse (D-17) |
| E | `RoutingKeys` contract and its cost (E-09); O(1) remount via `as_()` (E-14) |
| F | `to_dict` / `from_dict` and hashability for types in FSM data (F-12) |
| H | Identity within a view + seeding rule (H-13) |
| I | Build skeleton (I-01, I-05), build / size numbers and B25 calibration (I-06), stubtest / installed-wheel typing pattern (I-04) |
