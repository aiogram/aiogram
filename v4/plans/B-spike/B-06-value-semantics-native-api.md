# B-06 — Value semantics + native serialization API

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-05](B-05-views-cache-gc-routing-keys.md) |
| Blocks | [B-07](B-07-bound-views.md), [B-08](B-08-subclassing-register.md), [B-09](B-09-sendmessage-encoder-response.md), [B-11](B-11-cache-gc-teardown-ft-tests.md), [B-13](B-13-gate-run-and-decision.md), [F-12](../F-fsm/F-12-aiogram-types-in-fsmdata.md), [C-14](../C-butcher/C-14-pyi-stub-emitter.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [H-12](../H-testing-observability/H-12-toolkit-model-api-migration.md) |
| Gate-conditional | no |
| Decisions | D53, D84, D86, D87, D91–D95, D100, D108, D109, PD-02, PD-11, R05, R06 |
| Sources | [01-models.md §3.5–§3.7](../../research/01-models.md), [19 D108, D109, R05, R06, §8](../../research/19-review-resolutions.md), [13-aiogram-rust-review.md B2, B3, B17](../../research/13-aiogram-rust-review.md), [08-build-release.md §7 item 11](../../research/08-build-release.md), [14-testing.md D53](../../research/14-testing.md), [codex-review.md R05, R06](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

pydantic's `model_*` API is replaced by a wire-centric native API (D91–D95). R05 asked for one contract covering
wire-origin vs constructed / replaced objects, and D108 answered it. The spike must show these semantics hold on the
native layout. Several of them (cache seeding, eq / hash, pickle) interact with the cache and binding, and the
`to_dict` / `to_json` / pickle / re-mount benchmarks of 01 §5.2 need them.

## Scope

**In:**
- **Constructors.** Keyword-only (D100, PD-02); `text_signature` uses `...` for non-literal defaults (19 §8).
  - The constructor is **Python-value aware**: it accepts aiogram instances, `datetime`, `int`, tuples / lists, dicts
    in wire shape, and JSON-shaped extras (D87).
  - It does **not** round-trip through a dict. 08 §7 item 11's "`(**kwargs)` → `from_dict`" is read as "same
    validation core", not "build a dict first", because seeding needs the passed instances (R06).
- **Cache seeding (D53).** Objects passed to a constructor are placed in the child cache, so
  `Update(message=m).message is m` holds for unbound construction.
- **Native API.**
  - `to_json() -> bytes` and `to_dict()`: wire names, unix ints, no `None`, nested builtins, B2 interned keys.
  - `from_json(data, *, bot=None)` and `from_dict(d, *, bot=None)`.
  - `replace(**changes)` and `__replace__` (`copy.replace`, 3.13+): validates and drops the original bytes (D108).
  - All of this lives **once on a base**, dispatched through a per-type vtable (13 B3, 08 §7 item 11).
- **Raw for constructed objects (D108).** `.raw_json` returns canonical `to_json()` bytes for constructed or replaced
  objects; `.raw` returns a fresh dict.
- **Equality and hash (D84, D108).** Same class + equal data, **ignoring the bot binding**. An object is hashable only
  if all its fields are (raw and binding excluded); unhashable → `TypeError` naming the field.
- **`repr`.** Wire-free Python names, like 3.x.
- **Pickle.** `__reduce__` → `(type(obj)._from_json, (raw_json_bytes,))`; after `replace` the pickle carries the new
  canonical bytes (D108).
- **Extras (D87).** Must be JSON-shaped (`str` / `int` / `float` / `bool` / `None` / `list` / `dict`), else
  `TypeError`. Depth >128 → `ValueError`.
- **Input rules (B17 as revised by PD-11).**
  - Naive `datetime` is local time.
  - Fractional unix values round half-even (Python `round`, as 3.x `prepare_value` and `custom.DateTime` do).
  - `from` / `from_user` accepted on `from_dict` and the constructor.
  - **`timedelta` follows PD-11** (absolute `now + delta` at encode time, as 3.x
    `BaseSession.prepare_value` does). For *type* fields see the Decide item below; method parameters are B-09.
- **Reserved names (D109).** Exact names: `bot`, `raw`, `raw_json`, `to_json`, `to_dict`, `from_json`, `from_dict`,
  `replace`, `as_`, the `model_*` alias names. A constructor kwarg with a reserved name that is not a field raises
  `TypeError`.

**Out:**
- `as_()` and bound views (B-07). Registered subclasses (B-08).
- The deprecated `model_*` aliases (thin Python; wired with `aiogram.types`, C-18 / I-17).
- pydantic interop hooks (`__get_pydantic_core_schema__`, later).
- `model_fields` removal (D95, nothing to build).

## Checklist

- [ ] Keyword-only constructors with `text_signature`; a Python-value-aware validation core shared with `from_dict`.
- [ ] Decide seeding when a passed instance is **bound** (proposed default: seed only when the passed object's
  binding equals the new parent's, i.e. both unbound or the same bot object. Otherwise share the data `Arc`, build a
  fresh child view and lose identity, as R02 recommends and D103 implies). Record in Notes and flag to owner.
- [ ] `to_json` / `to_dict` / `from_json` / `from_dict` / `replace` / `__replace__` on the base vtable.
- [ ] Constructed-object `.raw_json` / `.raw` (D108).
- [ ] `__eq__` ignoring binding; `__hash__` only when all fields are hashable.
- [ ] Decide pickling a **bound** object (3.x raises, 19 corrections) (proposed default: pickle drops the binding and
  unpickles unbound, documented in the B-13 record as a candidate migration note. The binding is not data (D108) and
  FSM storage uses `to_dict` anyway). Record and flag.
- [ ] Decide pickle of registered subclasses with user state (proposed default: `__reduce__` uses `type(obj)`, so
  the subclass is kept; instance `__dict__` of a Python subclass, if any, is passed as the third reduce element and
  restored with `__setstate__`). Record and flag. Implemented with B-08.
- [ ] Decide `timedelta` in *type* DateTime fields (proposed default: rejected with `TypeError`, because 3.x pydantic
  `DateTime` fields on types reject it too; `timedelta` is only accepted on method parameters and resolved to
  `now + delta` at encode time per PD-11, in B-09). Record and flag.
- [ ] Extras validation (D87), depth check, B17 input rules (naive local, half-even, `from_user` alias).
- [ ] Register the `to_json` / `to_dict`, pickle round-trip and constructor workloads in the B-02 adapter.
- [ ] Tests in `tests/test_core/`, building the R05 acceptance table: wire-origin vs constructed vs replaced, each
  with a `to_json` / `from_json` round trip, a pickle round trip, `raw_json`, eq and set membership. Also: seeding
  identity, the bound-seeding rule, reserved-name `TypeError`, extras `TypeError` (100% of new Python).
- [ ] No changelog or registry entry here (not wired, PD-03). Breaking changes 1, 18, 19 and the D108 equality change
  get registry entries when wired (C-18 / I-17). List them in Notes for those plans.

## Acceptance criteria

- `Update(message=m).message is m` for an unbound `m`.
- For each of wire-origin, constructed and replaced objects: `T.from_json(x.to_json()) == x`,
  `pickle.loads(pickle.dumps(x)) == x`, and `x.raw_json` follows D108 (exact bytes, or canonical bytes). Equal objects
  hash equal and land in one set entry.
- Two equal updates bound to different bot objects compare equal (D108). An object with a list-typed extra raises
  `TypeError` on `hash()`.
- `Message(text="x", tag=object())` raises `TypeError` (D87).
- `inspect.signature(Message)` works (no `Default(...)` in `text_signature`).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| pydantic-shaped `model_*` as the primary API | Native wire-centric API; aliases deprecated | D91 |
| Public field introspection (`model_fields`, `fields()`) | Removed; can be added later without a break | D95 |
| Equality comparing bots by token (3.x) | Equality ignores binding | D108 (revises D84 hash wording) |
| `timedelta` as seconds | A bug: temporary bans would become permanent; 3.x sends `now + delta` | PD-11 (revises 13 B17, 05 §2.1, 01 §3.1) |
| `replace()` keeping the original bytes | Pickle / raw would show stale data | D108 |
| Prefix-based reserved names (`model_*`) | Exact names only; `UniqueGiftColors.model_custom_emoji_id` stays legal | D109 |
| Constructor via an intermediate dict | Loses seeding and Python-value inputs | R06, D53 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: B-05 views and cache.
- Outputs: the value-semantics contract used by F-12 (types in FSM data through `to_dict` / `from_dict`), H-13
  (seeding identity) and C-18 (base vtable shape).
- Can run in parallel with B-08, B-10 and B-11 once B-05 is merged. B-07 builds on the seeding rule decided here.

## Notes
