# F-14 — Typed scene data (`Scene.data: type[FSMData]`)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-09](F-09-fsmdata-typed-fsmcontext.md), [F-13](F-13-scenes-d33.md) |
| Blocks | [F-17](F-17-fsm-docs-migration-page.md) |
| Gate-conditional | no |
| Decisions | D30, D33, R16 |
| Sources | [04-fsm.md §7 Scenes, §8](../../research/04-fsm.md), [codex-review.md R16](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

04 §7: `Scene` subclasses may declare `data: type[FSMData]`, giving typed `self.wizard.get_data()`; the dict usage is
untouched. R16: a runtime class attribute is not enough; mypy and IDEs must infer the type.

## Scope

**In:**
- Typing mechanism: `SceneWizard` becomes generic in its data type (`SceneWizard[DataT]`, default `dict[str, Any]`
  via `typing_extensions.TypeVar(default=...)`), and `Scene` is generic too (`class Order(Scene[OrderForm],
  state="order")`), so `self.wizard.get_data()` is inferred as `OrderForm`. The `data` class attribute is derived from
  the generic argument (or declared explicitly as `data = OrderForm` for runtime use).
- Runtime: `wizard.get_data()` / `update_data(...)` / `set_data(...)` delegate to F-09's typed `FSMContext` overloads
  when `data` is set; otherwise unchanged dict behaviour.
- Docs example in `scene.rst`.

**Out:**
- Namespacing scene data (rejected, D33).

## Checklist

- [ ] Generic `Scene` / `SceneWizard` with a defaulted type variable (no change for existing non-generic scenes).
- [ ] Runtime delegation to typed overloads.
- [ ] Typing test (mypy run over a fixture file): `reveal_type(await self.wizard.get_data())` is `OrderForm` in a typed
      scene and `dict[str, Any]` in an untyped one.
- [ ] Runtime tests: typed and untyped scenes in the same router; `FSMDataError` on invalid stored data.
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- Existing scene tests pass unchanged.
- The mypy fixture passes with the project's strict config.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Runtime-only `data` attribute | No static inference | R16 |
| Separate per-scene storage namespace | Scene data stays shared with FSM data | D33 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- Last of the typed-data chain (F-08 → F-09 → F-14).

## Notes
