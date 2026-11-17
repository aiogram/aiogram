# I-17 — Codemod and checker rules: model semantics

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-15](I-15-receiver-inference.md), [C-26](../C-butcher/C-26-removal-inventory-signature-table.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [C-14](../C-butcher/C-14-pyi-stub-emitter.md) |
| Blocks | [I-20](I-20-examples-port-smoke.md), [I-22](I-22-migration-rehearsal.md), [I-23](I-23-beta-pre-release.md) |
| Gate-conditional | **yes** (D91–D95, D103, D106, D15 semantics follow the model gate, D104) |
| Decisions | D15, D87, D91–D96, D103, D105, D106, R06, R28 |
| Sources | [16-support-policy.md §2.2–2.3](../../research/16-support-policy.md), [01-models.md §3.3, §3.7](../../research/01-models.md), [19 D103, D105, D106, R06, R28](../../research/19-review-resolutions.md), [README breaking changes 1–3, 18–20, 22–23](../../research/README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Types stop being pydantic models. They become immutable (D15) and get a native wire-centric API (D91). Collections
become tuples (D106), and `as_()` returns a new view (D103).

These changes break code silently or at runtime, in places a reviewer can't easily grep for:
- `obj.x = y`;
- `msg.entities == [e]`;
- a bare `m.as_(bot)` statement;
- `model_dump(...)`;
- user `TelegramMethod` subclasses.

R28 sets the safety rule: `obj.x = y` may only become `obj = obj.replace(x=y)` on **plain names**, because the result
must be reassigned. Attribute chains and aliases are reported, never rewritten.

## Scope

**In.** Rules on the I-14 engine, using I-15 inference.

| Rule | Action | Class |
|---|---|---|
| Mutation of a type instance | `name.field = value`, where `name` infers to an aiogram type: → `name = name.replace(field=value)`. Consecutive writes to the same name merge into one `replace`. Attribute chains (`a.b.c = 1`), subscripts, augmented assignment (`+=`), names captured in closures, or a receiver that can't be inferred: report | definite fix (plain name, high confidence) / heuristic report |
| `model_dump` / `model_dump_json` / `model_validate` / `model_validate_json` / `model_copy` | → `to_dict` / `to_json` / `from_dict` / `from_json` / `replace`, only with kwargs in the alias subset (01 §3.7). `model_dump_json()` → `to_json().decode()` where the result is used as `str` (alias returns `str`, `to_json` returns `bytes`). `model_dump(by_alias=False)` default-key difference is reported (`to_dict` uses wire names) | definite for exact mappings, heuristic otherwise |
| `model_fields` / `model_json_schema` / other non-alias `model_*` | report (no replacement, D95) | definite report |
| `model_extra` / `__pydantic_extra__` | → `.raw` (report the shape difference) | heuristic |
| `MutableTelegramObject` imports/subclassing | report | definite report |
| User `TelegramMethod` subclasses | `class X(TelegramMethod[...])`: report with the `bot.call("method", {...}, returns=T)` recipe (D96) | definite report |
| Bare `x.as_(bot)` statement | an expression statement whose call is `.as_(...)` on an inferred aiogram object: → `x = x.as_(bot)` | definite fix (inferred) / heuristic report (uninferred `.as_` on unknown receivers; `MagicFilter.as_` is excluded via import tracking) |
| List comparisons on collection fields | `<collection field> == [...]` / `!= [...]` / `in [[...]]`: rewrite the literal list to a tuple; `.append` / `.extend` / `+=` / item assignment on a collection field: report | definite where the field is known (C-26 field table) |
| Non-JSON extras | constructor kwargs not in the type's field table whose value is a non-literal: report (D87) | heuristic |
| Unknown fields read as attributes | attribute names not in the 4.0 field table on a known receiver: report (D105 deprecation, works with a warning for one window) | heuristic |
| User subclasses of aiogram types (README breaking change 3) | `class X(Message)` / any class inheriting an aiogram type that is not passed to `aiogram.types.register(...)` anywhere in the project: report "decoded objects won't be `X` unless registered" with the `register` recipe (B-08) | heuristic |
| `isinstance(x, pydantic.BaseModel)` / `BaseModel` checks on aiogram objects | report | heuristic |
| pydantic models containing aiogram types | no finding (interop hooks keep working when the user installs pydantic, 01 §3.5) | — |

**Out:**
- `CallbackData` pydantic features (I-19).
- Positional calls (I-18).
- Removed Bot API fields (I-16).

## Checklist

- [ ] Rule modules `rules/mutation.py`, `rules/model_api.py`, `rules/views.py`, `rules/collections.py`, `rules/extras.py`.
- [ ] Field-kind table (collection fields per type) from C-26's collection-field map, loaded by path.
- [ ] Mutation rewrite: merge consecutive writes, preserve comments, and keep evaluation order (a value referencing
      another field of the same object must be evaluated before the reassignment, so report if unsure).
- [ ] Golden tests for each row, including the negative cases (chains, aliases, closures, `MagicFilter.as_`).
- [ ] Subclass rule: project-wide scan for classes inheriting an aiogram type, minus those passed to
      `aiogram.types.register(...)`; golden tests for registered / unregistered / aliased base.
- [ ] Registry ids from A-11's seed for README breaking changes 1, 2, 3, 18, 19, 20, 22 and 23. Fill in their
      codemod-coverage field.
- [ ] Re-validate every rule after B-13 against the final semantics (Notes line per rule: confirmed / changed).
- [ ] Tests (100% coverage of the rule modules).
- [ ] Changelog fragment `CHANGES/<id>.feature.rst` (migrate rules for the model API). Registry entries updated as above.

## Acceptance criteria

- Golden tests pass. Every `after` file passes `compile()`.
- No rewrite discards a `replace()` result: a test walks every golden `after` and asserts each `.replace(` call is the
  RHS of an assignment.
- `x.as_(bot)` as a bare statement on `message: Message` becomes `message = message.as_(bot)`. `F.data.as_("x")` is
  untouched.
- `msg.entities == [e]` (with `msg: Message`) becomes `msg.entities == (e,)`.
- `class MyMessage(Message)` without a `register(MyMessage)` call is reported (heuristic); with one, no finding.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `obj.x = y` → bare `obj.replace(x=y)` | Discards the result | R28 |
| Rewriting attribute chains (`a.b.c = 1`) | Needs nested `replace`, aliasing unsafe; report | R28 |
| Keeping `model_fields` as an alias | No public field introspection | D95 |
| Rebinding in place for `as_()` | Independent bound views | D103 |

## Validation

```bash
make dev
uv sync --extra migrate
uv run pytest tests/test_migrate -q
uv run pytest tests
uv run mypy aiogram
uv run python scripts/migration_registry.py check
make lint
```

## Workflow notes

- Inputs: I-15 (inference), C-26 (field tables), B-13 (go decision and final semantics).
- If B-13 is a no-go this plan is `blocked` and re-planned with the redesigned model layer.
- Outputs: rules used by I-20 / I-22 rehearsals.

## Notes

(empty)
