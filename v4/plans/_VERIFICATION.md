# Plan verification report (2026-11-17)

## Method

1. **Scripted graph check**, run after every fix round. It confirms that every `Depends on`/`Blocks` id exists and that
   every edge appears on both sides. It also finds dependency cycles and gate-transitive dependencies.
2. **Three independent read-only verifiers** looked at the plans from different angles:
   - **coverage**: D1–D121, PD-01..34, breaking changes 1–24, 11-removals and the 19 §2 R-items each have an owner,
     and nothing has two owners;
   - **cross-plan contracts**: APIs, ordering, defaults and branches;
   - **quality and handoff readiness**: template compliance, links, sizing, a 22-plan self-containment sample, and the
     story READMEs.
3. **Two fix rounds**, then a **fresh re-verifier** that checked the fixes and the split plans. A third round fixed the
   13 leftovers it reported.

## Result

| Check | Result |
|---|---|
| Plans | 204 in 11 stories (H-03 merged into D-03; I-13 merged into 3x-20..3x-24) |
| Unknown ids / asymmetric edges / cycles | 0 / 0 / 0 |
| Broken relative links | 0. `_TEMPLATE.md` links resolve once it is copied into a story folder |
| Template sections | all present in all plans |
| Coverage | every decision that needs work has an owner; withdrawn and deferred items are recorded as rejected |
| Gate-conditional | 30 yes, 6 partial, 168 no. 29 `no` plans depend on a gate-conditional plan and are blocked until it lands (README semantics); their *Workflow notes* say what can start early |
| Rough effort | ≈520 person-days. Critical path ≈100 working days with unlimited parallelism. The B gate is reachable after ≈43 days |

## Resolutions applied during verification

The coordinator settled these as defaults. The touched plans record each one in *Notes*:

- the i18n capture point is the E-02 handler-result seam;
- there is one per-update context carrier, owned by H-01;
- E-11 handles errors inside the FSM scope;
- C-26 runs on dev-3.x and writes no registry entries;
- `LazyText` is a Protocol in `aiogram/_lazy.py`;
- the Rust content-kind table is owned by C-19;
- `model_*` aliases are owned by C-18;
- `ErrorPhase` has no RETRY;
- RequestLogging stays on `aiogram.middlewares` for one window.

Splits for PR size:

- E-13 → E-13 + E-23
- E-19 → E-19 + E-22
- B-03 → B-03 + B-14
- J-04 → J-04 + J-08

## Known residual risks (not conflicts)

- **PD-06 vs PD-09.** Single-bot sharding ships in 4.0, but Redis/Mongo stay single-loop, so sharded deployments with
  Redis can't share one storage. This is an owner question in F-06 *Notes*.
- **162 `Decide …` items** are open (held-back plans not counted). See [_DECISIONS.md](_DECISIONS.md). Each has a proposed default, so implementation
  can proceed, and the owner can override any of them.
- **Embargo (PD-34).** The committed `v4/` is redacted; held-back plans are committed after their fixes ship.
