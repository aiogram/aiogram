# F-10 — Optional `PydanticAdapter`, `AttrsAdapter`, `MsgspecAdapter`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-09](F-09-fsmdata-typed-fsmcontext.md) |
| Blocks | [F-17](F-17-fsm-docs-migration-page.md) |
| Gate-conditional | no |
| Decisions | D14, D30 |
| Sources | [04-fsm.md §7 Pluggable adapters](../../research/04-fsm.md), [11-removals.md §4 No pydantic dependency](../../research/11-removals.md), [07-free-threading.md §4](../../research/07-free-threading.md), [codex-review.md R16](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D30: users with existing models (pydantic `BaseModel`, attrs classes, msgspec `Struct`) can use them as FSM data once
the adapter is registered: `Dispatcher(fsm_data_adapters=[PydanticAdapter()])`, then
`await state.get_data(MyPydanticModel)`. The adapters ship in core and import their library lazily; aiogram gains no
dependency (D14).

## Scope

**In:**
- `aiogram.fsm.data.adapters` with three classes implementing F-09's `DataAdapter`:
  - `PydanticAdapter`: `supports` = subclass of `pydantic.BaseModel`; `load` = `model_validate`; `dump` =
    `model_dump(mode="json")`; partial patch support via `model_fields_set` (D115 `exclude_unset`).
  - `AttrsAdapter`: `attrs.has(tp)`; `load` via `tp(**converted)` using F-08 converters on `attrs.fields` types;
    `dump` via `attrs.asdict` + JSON codec.
  - `MsgspecAdapter`: `msgspec.Struct` subclasses; `msgspec.convert` / `msgspec.to_builtins`.
- Lazy import: importing `aiogram.fsm.data.adapters` must not import the libraries; constructing an adapter whose
  library is missing raises `ImportError` with an install hint.
- Load errors are wrapped in `FSMDataError` (F-09) with `.raw`.
- Test dependency group in `pyproject.toml` gains `pydantic`, `attrs`, `msgspec` (test-only; lower bounds only, D70),
  so the 100% coverage rule holds. Coordinate with I-07.

**Out:**
- Adapters for other libraries (users implement the protocol).
- A `aiogram[pydantic]` extra: rejected (D14).

## Checklist

- [ ] Three adapters with lazy imports.
- [ ] Partial-patch semantics for each adapter documented (what "explicitly set" means per library).
- [ ] Test group dependencies; tests skip with `pytest.importorskip` when a library is missing (e.g. msgspec without
      3.14t wheels); CI coverage is measured on a job that has all three.
- [ ] One round-trip test per adapter plus a typed patch test and an `FSMDataError` test.
- [ ] `python -X importtime -c "import aiogram.fsm.data.adapters"` shows none of the three libraries.
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- With each library installed, `get_data(Model)` / `update_data(Model, field=...)` / `set_data(instance)` round-trip
  on MemoryStorage and the Redis mock.
- Without the libraries, `import aiogram` and `import aiogram.fsm.data.adapters` succeed.
- `pip install aiogram` resolves no pydantic/attrs/msgspec.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Separate distributions per adapter | Small code, no dependency; lives in core with lazy imports | 04 §7 |
| Optional extras that pull the libraries | Users already depend on their model library | D14 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- Parallel with F-11, F-12, F-14 once F-09 lands.

## Notes
