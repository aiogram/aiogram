# F-09 — `FSMData` and the typed `FSMContext` API (typed patches, adapters protocol)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-08](F-08-shared-converter-core.md) |
| Blocks | [F-10](F-10-pydantic-attrs-msgspec-adapters.md), [F-12](F-12-aiogram-types-in-fsmdata.md), [F-14](F-14-typed-scene-data.md), [F-17](F-17-fsm-docs-migration-page.md) |
| Gate-conditional | no |
| Decisions | D30, D115, R16 |
| Sources | [04-fsm.md §7](../../research/04-fsm.md), [19 D115](../../research/19-review-resolutions.md), [codex-review.md R16](../../research/codex-review.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D30: typed FSM data with nested types and pluggable adapters, while the dict API stays. D115: typed **patches**:
`update_data(OrderForm, qty=2)` validates each field without a full model, passing a model instance merges only
explicitly set fields, mutable defaults are copied per instance, `set_data(model)` writes the full model. Storage
stays dict-based: conversion happens at the `FSMContext` boundary (`aiogram/fsm/context.py`).

```python
form = await state.get_data(OrderForm)               # -> OrderForm (validated)
await state.update_data(OrderForm, qty=2)            # typed patch (D115)
await state.update_data(OrderForm(item_id=5))        # merges only explicitly set fields
await state.set_data(form.replace(qty=2))            # full model
await state.get_data()                               # dict API unchanged
```

## Scope

**In:**
- `aiogram.fsm.data.FSMData`: `typing.dataclass_transform`, frozen, keyword-only constructor, `replace(**changes)` +
  `copy.replace`, `__eq__`/`__repr__`, built on the F-08 field specs and the JSON codec.
- `FSMContext` overloads (typed with `@overload` so mypy infers the return type):
  - `get_data() -> dict[str, Any]` (unchanged); `get_data(tp: type[T]) -> T`;
  - `update_data(data: Mapping | None = None, **kw) -> dict` (unchanged); `update_data(tp: type[T], **patch) -> T`
    (each patch field validated, unknown names raise); `update_data(instance) -> type(instance)` (merges only set
    fields, `exclude_unset`);
  - `set_data(Mapping)` unchanged; `set_data(instance)` writes the full dump.
  - Keys the model doesn't declare are ignored on load and kept on `update_data`.
- Name: the 3.x `FSMData` **TypedDict** in `aiogram/dispatcher/middlewares/data.py` is renamed `FSMKeysData` by
  E-20 (no alias), so `FSMData` means only this class in 4.0; the FSM docs and migration notes say so.
- `FSMDataError(Exception)` carrying `.raw` (the stored dict) and the field path; handlers can reset state.
- `DataAdapter` protocol (`supports(tp)`, `load(tp, data)`, `dump(obj)`) with built-ins for `FSMData` and stdlib
  dataclasses. Selection: first adapter whose `supports(tp)` is true from the user list, built-ins appended.
- `Dispatcher(fsm_data_adapters=[...])` → `FSMContextMiddleware` → every `FSMContext` it creates.
- Docs page section with the examples above and schema-evolution guidance (R16): adding a field with a default,
  removing a field (ignored), renaming (needs a manual step), what raises `FSMDataError`.

**Out:**
- pydantic/attrs/msgspec adapters: [F-10](F-10-pydantic-attrs-msgspec-adapters.md).
- aiogram types as fields: [F-12](F-12-aiogram-types-in-fsmdata.md).
- Typed `Scene.data`: [F-14](F-14-typed-scene-data.md).

## Checklist

- [ ] Decide whether typed dumps are JSON-shaped in every storage, including MemoryStorage (**proposed default:**
      yes, `FSMData`/adapter dumps are always JSON-shaped (`datetime` → ISO string, `Decimal` → string) so a model
      round-trips identically on Memory, Redis and Mongo and tests on Memory predict production. The plain dict API
      keeps storing arbitrary Python objects in MemoryStorage, 04 §5) — record in Notes and flag to owner.
- [ ] Decide how adapters reach a manually built `FSMContext` (**proposed default:** `FSMContext(storage, key,
      adapters=None)`; contexts created by the middleware (and `dp.fsm.get_context(...)`) get the dispatcher's list; a
      manual `FSMContext` without `adapters=` gets only the built-ins and, for an unsupported type, raises `TypeError`
      naming the missing adapter. No module-global registry (thread safety, test isolation)) — record in Notes and
      flag to owner.
- [ ] `FSMData` class on F-08.
- [ ] Docs/migration note: the 3.x `FSMData` TypedDict is now `FSMKeysData` (E-20 owns the rename and its registry
      entry).
- [ ] `FSMContext` overloads + `FSMDataError`.
- [ ] `DataAdapter` protocol + built-ins + dispatcher wiring.
- [ ] Typing tests: a `tests/typing/` (directory from B-01; create if absent) case asserting `reveal_type(await state.get_data(OrderForm))` is
      `OrderForm`, and that the dict overloads still infer `dict[str, Any]`. Note in docs that `update_data(tp, **patch)`
      kwargs are validated at runtime only (no static check of patch names).
- [ ] Tests: typed patch keeps unrelated stored keys; `OrderForm(item_id=5)` merge does not overwrite a stored `qty`;
      mutable default isolation (two instances, mutate one's list); nested round trip; `FSMDataError.raw`; storage
      parity Memory vs Redis mock vs Mongo mock.
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/` (additive feature).

## Acceptance criteria

- The 04 §7 example runs as a test against MemoryStorage and both mocked remote storages with identical results.
- `update_data(OrderForm(item_id=5))` on stored `{"item_id": 1, "qty": 3, "extra": "x"}` yields
  `{"item_id": 5, "qty": 3, "extra": "x"}`.
- mypy (strict, project config) infers `OrderForm` for `get_data(OrderForm)`.
- Dict-API tests in `tests/test_fsm/test_context.py` pass unchanged.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Typed data stored in a separate key/layout | Storage stays dict-based; layouts unaffected | 04 §7 |
| `update_data(model)` overwriting with defaults | Defaults would clobber stored values | D115 |
| pydantic as the built-in model | Not a dependency | D14 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm tests/test_utils -q
uv run pytest tests
make lint
```

## Workflow notes

- Needs F-08's field specs and codec. E-20 renames the 3.x `FSMData` TypedDict to `FSMKeysData`; do not reuse or
  alias the old TypedDict. F-10, F-12 and F-14 build on the adapter protocol and overloads.
- R16 asks to estimate typed data as its own subsystem: if this runs over L, split typed patches into a follow-up and
  record it in Notes.

## Notes
