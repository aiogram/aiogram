# F-11 — `CallbackData` without pydantic (D14)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-08](F-08-shared-converter-core.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [F-17](F-17-fsm-docs-migration-page.md), [I-07](../I-distribution/I-07-dependencies-extras-restructure.md), [I-19](../I-distribution/I-19-heuristic-behaviour-rules.md) |
| Gate-conditional | yes *(D104 lists D14; re-validate after B-13)* |
| Decisions | D14, D30 (shared converters), D104, README breaking change 12 |
| Sources | [11-removals.md §4](../../research/11-removals.md), [06-utils.md §2](../../research/06-utils.md), [04-fsm.md §7](../../research/04-fsm.md), [09-3x-quick-wins.md #16](../../research/09-3x-quick-wins.md), [16-support-policy.md](../../research/16-support-policy.md), [19 D104](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`aiogram/filters/callback_data.py` (3.x) subclasses `pydantic.BaseModel`. D14 makes `CallbackData` a
dataclass-style class with the **same declaration syntax**, so pydantic is no longer a dependency. The rewrite is pure
Python on the F-08 flat-string codec. It is gate-conditional only because D104 lists D14: if B-13 is a no-go and the
types stay pydantic, rewriting `CallbackData` is a gratuitous break.

**Why this lives in F:** D30 mandates one converter table shared by `CallbackData` and `FSMData`. Building them in
different stories would either duplicate the converter or make one story wait on a half-built module. Removing
pydantic from `pyproject.toml` is **not** this plan: it needs every type off pydantic (B/C), and the packaging edit is
I-07.

```python
class Item(CallbackData, prefix="item"):
    id: int
    kind: ItemKind          # Enum
    page: int | None = None
```

## Scope

**In:**
- `CallbackData` on F-08: `dataclass_transform`, class kwargs `prefix=` (required) and `sep=` (default `:`), the
  same class-creation errors (missing prefix, separator inside prefix).
- `pack()`: field order = declaration order; encoding rules identical to 3.x `_encode_value` (`None` → `""`, `Enum`
  → `str(value.value)`, `UUID` → `.hex`, `bool` → `"1"`/`"0"`, `int`/`str`/`float`/`Decimal`/`Fraction` → `str`);
  separator-in-value error; the 64-byte limit (`MAX_CALLBACK_LENGTH`).
- `unpack()`: **prefix fast-fail before split and convert** (09 #16); part-count `TypeError`; the 3.x empty-part rule
  (#2007: an empty part means `None` when the field accepts `None`, even if its default is something else; a
  non-nullable field with a default takes the default; a `""` default stays `""`).
- Conversion errors are `ValueError` / `TypeError` subclasses, because `CallbackQueryFilter.__call__` catches exactly
  those (pydantic's `ValidationError` was a `ValueError`).
- `filter(rule)` and `CallbackQueryFilter` unchanged; `F` rules resolve on the instance attributes.
- Equality, hash (frozen instances are hashable), `repr`, pickle.
- Migration guide entry: pydantic `Field(...)`, validators and `model_*` methods are gone; replace a validator with a
  `__post_init__` check (example).

**Out:**
- Dropping pydantic from dependencies: I-07 (after B/C).
- The 3.x prefix fast-fail: 3x-14 on `dev-3.x` (not a dependency).
- Checker rules that flag `Field(...)` / validators on `CallbackData` subclasses: I-16 / I-19 consume the registry entry.

## Checklist

- [ ] Decide lax coercion when unpacking (**proposed default:** accept exactly what 3.x pydantic lax mode accepted for
      the flat types, verified by a differential test against the pinned 3.x venv (PD-12) over a corpus of hand-written
      callback strings, e.g. `bool` from `"1"/"0"/"true"/"false"/"yes"/"no"/"on"/"off"` case-insensitive, `int` from
      integer strings only; any input 3.x accepted and 4.0 rejects is listed in Notes and in the migration entry) —
      record in Notes and flag to owner.
- [ ] Rewrite `aiogram/filters/callback_data.py` without pydantic imports.
- [ ] Port and extend `tests/test_filters/test_callback_data.py`: every existing case passes; empty-part matrix
      (#2007); fast-fail on a wrong prefix does no conversion (patched converter not called); 64-byte limit; pickle.
- [ ] Differential test vs 3.x pack/unpack (A-07 framework) over the corpus.
- [ ] Benchmark (A-05): `pack` / `unpack` of `Item` and a non-matching filter call.
- [ ] Tests (100% coverage of new code)
- [ ] Migration-registry entry (PD-13, `removal-4.0`): pydantic features on `CallbackData` (`Field`, validators,
      `model_*`) removed; `__post_init__` recipe.
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- `rg -n "pydantic" aiogram/filters/callback_data.py` is empty.
- For every corpus value, 4.0 `pack()` output equals 3.x output byte for byte, and `unpack()` agrees with 3.x except
  for documented differences.
- Non-matching `CallbackQueryFilter` call ≤ 0.3 µs (3.x without fast-fail ≈8 µs; 09 #16 target 0.2 µs) on the A-05
  reference machine.
- `pack` / `unpack` of `Item` ≤ the 3.x baselines (2.3 / 2.9 µs, A-06).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep `CallbackData` on pydantic | pydantic dropped as a dependency | D14 |
| Rust pack/unpack | Cost is user field conversion; fast-fail removes most filter cost | 11 §4 |
| An `aiogram[pydantic]` extra for compatibility | No pydantic dependency, required or optional | D14 |
| Own converter separate from FSMData | One shared table | D30 |

## Validation

```bash
make dev
uv run pytest tests/test_filters -q
uv run pytest tests
make lint
```

## Workflow notes

- Runnable only after B-13 records a go (gate-conditional). Code can be prepared earlier on a branch.
- Unblocks I-07 (pydantic removal from dependencies) together with the B/C model work.

## Notes
