# H-20 — Integration test layer, examples smoke harness, H exit gate

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-02](H-02-token-redaction-filter.md), [H-05](H-05-trace-hook-core.md), [H-13](H-13-binding-identity-rewrite.md), [H-14](H-14-delivery-through-runner.md), [H-15](H-15-route-diagnostics-on-trace-hook.md), [H-16](H-16-fake-fidelity.md), [H-17](H-17-toolkit-feature-interop.md), [H-18](H-18-toolkit-docs.md), [H-19](H-19-mockedbot-port.md), [E-21](../E-runtime/E-21-e-exit-gate.md), [F-16](../F-fsm/F-16-race-suite-314t.md) |
| Blocks | [I-20](../I-distribution/I-20-examples-port-smoke.md), [J-01](../J-ga/J-01-feature-inventory-audit.md), [I-23](../I-distribution/I-23-beta-pre-release.md) |
| Gate-conditional | yes |
| Decisions | D88, R26, D121, PD-01 |
| Sources | [14-testing.md §3 "Dogfooding"](../../research/14-testing.md), [README milestone H](../../research/README.md), [codex-review.md §9 milestone H, R26](../../research/codex-review.md), [18-docs-migration.md (examples run in CI)](../../research/18-docs-migration.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone H's exit gate (README D121, plans README §2) has three parts:
- redaction tests pass;
- tracer-failure tests pass;
- the toolkit uses **only public extension points**, so production code can be exercised without the fake.

D88 adds a toolkit-driven integration layer for aiogram's own suite. 18 runs the rewritten `examples/` in CI
through the toolkit. This task builds the first integration tests and the examples smoke harness, and records the
gate.

## Scope

**In:**
- `tests/test_integration/`: end-to-end toolkit scenarios across subsystems, using the toolkit only. Scenarios:
  - command → FSM state → scene transition;
  - filter rejection falls through to the next router;
  - a handler error bubbles to the parent router's `errors` handler (D48);
  - default isolation serialises two updates of one user (D28);
  - `release_isolation` for "ask and wait" (D110);
  - `Depends` with teardown inside the isolation scope (PD-04);
  - unknown update to `unknown_update`;
  - flood plus Retry.
- Examples smoke harness in `tests/test_examples/` (the runner path I-20 uses): a pytest helper that loads an `examples/<name>.py` module's dispatcher or routers into a
  toolkit env and runs a scripted conversation. **Examples split (agreed with I-20):** this plan builds the smoke helper and ports + wires exactly 3 polling-style
  examples (proposed `echo_bot.py`, `finite_state_machine.py`, `scene.py`; record the final three in *Notes*); I-20
  ports the remaining examples and registers them with this helper.
- **Exit-gate check:**
  - **Decide the H exit-gate check** (proposed default: (a) an AST test asserts `aiogram/test/**` imports no
    `aiogram` module or attribute whose name starts with `_`, outside `aiogram.test` itself and the generated
    `aiogram/test/_tables.py`; (b) a test asserts the toolkit never assigns attributes on aiogram classes or
    modules (no monkeypatching: AST scan for `setattr`/attribute assignment on imported aiogram names);
    (c) the H-02 redaction suite and the H-05/H-06 tracer-failure suites are required jobs in CI). Record the
    decision in *Notes* and flag it to the owner.
  - Gate record: a short section in this plan's *Notes* when done, listing the three checks with links to the
    passing CI run.

**Out:**
- Porting and registering every example except the 3 wired here (I-20).
- Production-path (non-fake) tests of each subsystem: each story's own suite, with MockedBot (H-19).

## Checklist

- [ ] `tests/test_integration/` with the scenarios above.
- [ ] Examples smoke helper plus 3 examples ported and wired (names recorded in *Notes* for I-20).
- [ ] Exit-gate decision and its checks (a)–(c) implemented as tests and CI requirements.
- [ ] Gate record in *Notes*.
- [ ] No changelog (tests only).

## Acceptance criteria

- All integration scenarios pass on 3.11–3.15 in the normal CI matrix. On 3.14t they pass in a single-loop setup,
  because the toolkit is single-loop (14 §3).
- Checks (a) and (b) fail on a deliberate violation (negative tests).
- The redaction (H-02) and tracer-failure (H-05/H-06) suites are green and marked required.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Mass-rewriting unit tests onto the toolkit | No mass rewrite | D88 |
| Toolkit-private hooks into the dispatcher | Violates the exit gate; production paths would only be tested through the fake | milestone H |
| Counting coverage % as the gate | Coverage is not correctness | R26 |

## Validation

```bash
make dev
uv run pytest tests/test_examples -q
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Last H task. Gate-conditional through H-13/H-16/H-17.
- Inputs: all toolkit tasks, E-21 (E exit gate), F-16 (FSM race suite).
- Outputs:
  - the examples smoke helper and the 3 wired examples (I-20 ports and registers the rest);
  - the H gate record (J-01 feature inventory).

## Notes
