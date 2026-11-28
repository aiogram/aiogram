# F-08 — Shared converter core (FSMData + CallbackData)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md) |
| Blocks | [F-09](F-09-fsmdata-typed-fsmcontext.md), [F-11](F-11-callbackdata-without-pydantic.md) |
| Gate-conditional | no |
| Decisions | D14 (shared table), D30, D115, R16 |
| Sources | [04-fsm.md §7](../../research/04-fsm.md), [11-removals.md §4](../../research/11-removals.md), [codex-review.md R16](../../research/codex-review.md), [19 D115](../../research/19-review-resolutions.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D30 adds typed FSM data and D14 rewrites `CallbackData` without pydantic. 04 §7 mandates **one converter table**:
`CallbackData` uses its flat-string subset, `FSMData` the JSON-shaped nested superset, both built at class creation so
there is no per-call reflection. R16 warns this is a validation subsystem, not a small table: it needs a contract
suite, default handling, recursion and field-path errors. This plan builds that core with no dependency on the model
layer (the B gate) or on pydantic, so F-09 can ship whatever the gate decides.

## Scope

**In:**
- Internal module `aiogram/utils/_converters.py` (name may change; keep it private):
  - class-creation compiler: resolves annotations (`typing.get_type_hints(include_extras=True)`, forward refs,
    `from __future__ import annotations`) into a tuple of field specs `(name, converter, default | default_factory)`;
  - **types:** `str`, `int`, `float`, `bool`, `Decimal`, `UUID`, `Enum` / `IntEnum` / `StrEnum`, `datetime`, `date`,
    `X | None`, `Literal[...]`, `list[T]`, `tuple[T, ...]`, `dict[str, T]`, nested converter-backed classes, stdlib
    dataclasses; `Fraction` per the decision below;
  - **two codecs per converter:** `to_str` / `from_str` (flat-string subset for callback data: scalars, enums,
    `Literal`, `X | None`) and `to_json` / `from_json` (JSON-shaped values: `str`/`int`/`float`/`bool`/`None`/`list`/
    `dict[str, ...]`; `datetime` as ISO 8601, `Decimal` as `str`, `UUID` as canonical `str`);
  - unsupported annotation → `TypeError` at **class creation**, naming the class and field;
  - errors at load time carry a **field path** (`address.zip`, `tags[2]`) and the offending value.
- Default handling: immutable defaults shared; mutable defaults (`[]`, `{}`, `set()`) copied per instance (D115);
  a "set fields" record per instance so `exclude_unset` works (D115).
- Recursive types (a class referring to itself through `X | None` or `list[X]`) resolve lazily without infinite
  compile loops.
- An **independent converter contract suite** (R16) in `tests/test_utils/test_converters.py`: per type, both codecs,
  round trip, rejected inputs, field paths, defaults, recursion.

**Out:**
- The `FSMData` class and `FSMContext` API: [F-09](F-09-fsmdata-typed-fsmcontext.md).
- `CallbackData` itself: [F-11](F-11-callbackdata-without-pydantic.md) (gate-conditional).
- aiogram types as fields: [F-12](F-12-aiogram-types-in-fsmdata.md) (gate-conditional). The core must expose a hook
  for registering extra converters so F-12 can add them without changes here.
- Third-party model adapters: [F-10](F-10-pydantic-attrs-msgspec-adapters.md).

## Checklist

- [ ] Decide `Fraction` support (**proposed default:** support `Fraction` in both codecs, encoded as `str(value)`
      (`"1/3"`) and decoded with `Fraction(text)`, because 3.x `CallbackData._encode_value` accepts it and dropping it
      would be an unlisted break; 11 §4's list omits it) — record in Notes and flag to owner.
- [ ] Compiler + field specs; class-creation errors.
- [ ] Converters for every type in Scope; flat-string subset enforced (non-flat types rejected for `to_str`).
- [ ] Default/mutable-default/`exclude_unset` support.
- [ ] Extension hook for extra converters (used by F-12), keyed by exact type, checked before the built-ins.
- [ ] Contract suite (R16) and a micro-benchmark (A-05 harness): load of a 5-field flat class from JSON-shaped dict.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- The contract suite covers every type × codec × {valid, invalid} and passes.
- Unsupported annotations fail at class creation, not at first use.
- Loading a 5-field flat class (int, str, Enum, `int | None`, bool) from a dict ≤ 3 µs on the A-05 reference machine
  (3.x pydantic `CallbackData.unpack` is 2.9 µs; record the measured number in Notes).
- No import of pydantic, attrs, msgspec or `aiogram._core` in the module (`python -X importtime` check in a test).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep pydantic for validation | pydantic is no longer a dependency | D14 |
| Separate converters for CallbackData and FSMData | One table, flat subset vs JSON superset | D30, 04 §7 |
| Per-call reflection over annotations | Cost; table is built at class creation | 04 §7 |
| Rust converters | User field conversion dominates; no gain | 11 §4 |

## Validation

```bash
make dev
uv run pytest tests/test_utils -q
uv run pytest tests
make lint
```

## Workflow notes

- Parallel with F-01, F-02, F-04. F-09 and F-11 both build on it; keep the field-spec API stable once merged.

## Notes
