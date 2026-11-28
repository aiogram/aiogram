# Story H — Testing & observability

**Goal:**
- Port the Testing World toolkit (PR #1887) to 4.0 as `aiogram.test`, with the auto-loaded plugin (D51–D54, D88, D89).
- Ship the official trace hook as sync span context managers (D63, R23) and opt-in OpenTelemetry traces and metrics
  (D64).
- Ship structured logging and a consistent logger hierarchy (D65).
- Turn token redaction on by default (D66, R22).
- Keep `MockedBot` working as the unit-test tool across the model and codec switch (D88).

**Exit gate** (README D121, plans README §2):
- redaction tests pass;
- tracer-failure tests pass;
- the toolkit uses only public extension points.

H-20 records it. The concrete check is a pending decision in H-20.

**Merged task:** H-03 (token-free exception text) is part of [D-03](../D-client/). H-02 relies on it for the
exception guarantee. `Bot.__repr__` belongs to D-01.

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [H-01](H-01-logger-hierarchy.md) | Logger hierarchy + structured log context | A-01, A-11 | no | M |
| [H-02](H-02-token-redaction-filter.md) | Token redaction filter | D-03, H-01 | no | M |
| [H-04](H-04-access-log-redaction.md) | Access-log redaction wiring | E-16, E-17, H-02 | no | S |
| [H-05](H-05-trace-hook-core.md) | Trace hook core (protocol, calling rules, adapter) | A-01 | no | M |
| [H-06](H-06-tracing-in-executor.md) | Tracing in the snapshot executor | A-05, E-02, E-03, G-02, H-01, H-05 | no | L |
| [H-07](H-07-api-call-spans.md) | API_CALL spans (per attempt, inside Retry) | D-02, D-06, D-11, G-13, H-05, H-19 | no | S |
| [H-08](H-08-otel-traces.md) | `aiogram[otel]`: traces | E-23, H-06, H-07, I-07 | no | M |
| [H-09](H-09-otel-metrics.md) | `aiogram[otel]`: metrics with bounded labels | H-08 | no | M |
| [H-10](H-10-testing-world-import.md) | Testing World import + packaging | A-01 | no | M |
| [H-11](H-11-generated-toolkit-tables.md) | Generated toolkit tables + fake-coverage guard | C-01, C-08, C-16, D-13, H-10 | no | M |
| [H-12](H-12-toolkit-model-api-migration.md) | Model-API migration inside the toolkit | B-06, C-13, C-18, D-10, D-12, H-10, H-11 | **yes** | L |
| [H-13](H-13-binding-identity-rewrite.md) | Binding and identity rewrite (bound views) | B-05, B-07, B-13, H-12 | **yes** | M |
| [H-14](H-14-delivery-through-runner.md) | Toolkit delivery through the Runner | E-03, E-04, E-12, E-13, E-14, E-23, H-10 | no | M |
| [H-15](H-15-route-diagnostics-on-trace-hook.md) | Route diagnostics on the trace hook | E-11, G-02, H-05, H-06, H-14 | no | S |
| [H-16](H-16-fake-fidelity.md) | Fake fidelity: modelled vs synthesised, trace replay, manifests | A-04, A-07, D-15, H-02, H-12 | **yes** | M |
| [H-17](H-17-toolkit-feature-interop.md) | Toolkit interop (flood/retry, Unknown, ErrorReason, i18n) | C-19, D-02, E-05, F-03, G-02, G-06, G-13, G-14, H-12, H-14 | **yes** | M |
| [H-18](H-18-toolkit-docs.md) | Toolkit and observability docs (4.0 structure) | H-14, H-15, H-17, I-10 | no | M |
| [H-19](H-19-mockedbot-port.md) | Port `MockedBot` / `MockedSession` + suite strategy | A-01 | no | M |
| [H-20](H-20-integration-layer-exit-gate.md) | Integration layer, examples smoke harness, H exit gate | E-21, F-16, H-02, H-05, H-13, H-14, H-15, H-16, H-17, H-18, H-19 | **yes** | M |

## Order and parallel lanes

```
early (PD-31):   H-19   H-01 ─▶ H-02            H-10            H-05 (after E-03)
observability:   H-02 ─▶ H-04 (after E-16/E-17/G-16)
tracing:         H-05 ─▶ H-06 ─▶ H-08 ─▶ H-09
                 H-05 ─▶ H-07 ─┘
toolkit:         H-10 ─▶ H-14 ─▶ H-15
                 H-10 ─▶ H-11 ─▶ H-12* ─▶ H-13* ─┐
                                 H-12* ─▶ H-16* ─┤
                          H-14 + H-12* ─▶ H-17* ─┴─▶ H-18 ─▶ H-20* (exit gate)
(* gate-conditional)
```

1. **Start immediately after A-01:** H-19, H-01 (with A-11), H-10. Then H-02 after H-01. H-05 starts as soon as
   E-03 provides the epoch containers (PD-18).
2. **Tracing lane** follows E-02 (H-06) and D-06/G-13 (H-07). OTel (H-08/H-09) follows both.
3. **Toolkit lane:**
   - H-14/H-15 don't depend on the gate and can land on the 3.x-derived types;
   - H-12/H-13/H-16/H-17 wait for B-13 *go* and the C-13/C-18 type switch.
4. **H-20** closes the story.

## Pending owner decisions (proposed defaults in the plans)

| Decision | Plan |
|---|---|
| SpanKind gaps: DECODE/DEPENDENCY kinds, isolation wait. Proposed: attributes, no new kinds | H-05 |
| Default `exclude` for OTel. Proposed: FILTER spans off by default | H-08 |
| `router` metric label for unnamed routers | H-09 |
| #1887 shipping status in 3.x. Decided: shipped in 3.33.0, plugin auto-loaded (D51 revised); no PD-13 entry | H-10 |
| `BOT_RIGHTS` stays hand-written, guarded | H-11 |
| Per-receiving-bot identity scope | H-13 |
| Sync `bot_env` fixture vs async lifecycle. Proposed: sync + `async with env.running()` | H-14 |
| Rejection texts stay in `rejections.py` | H-17 |
| H exit-gate check. Proposed: AST checks (no private imports, no monkeypatching) + required CI suites | H-20 |

**Proposed defaults that correct 19** (flag to the owner):
- `setup_application` attaches the redaction filter to the `aiohttp.access` logger (H-04);
- the redaction filter also scrubs string `extra` attributes (H-02/H-04).

## Notes for other stories

- **E-02:** writes router/handler/phase into the H-01 log context and calls the H-05 helper at stage seams.
- **E-03:** provides the epoch-bumping `dp.tracers` / `dp.dependency_overrides` (PD-18).
- **D-10:** must expose a Python-callable resolve/render step that returns a resolved method, not bytes. H-12
  reuses it instead of a second resolver.
- **G-13:** writes the per-attempt number into D-06's per-call request context, where H-07 reads it (PD-17).
- **G-02:** runs teardown through a seam H-06 can wrap.
- **C-06:** no longer lists "fake marks" in the overlay; the H-11 pytest guard replaces them.
- **I-20:** ports examples onto the smoke helper from H-20.
