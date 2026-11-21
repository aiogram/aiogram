# F-08 — Shared converter core (FSMData + CallbackData)

| Field | Value |
|---|---|
| Status | `done` |
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
- **Added by PD-35 (owner, 2026-11-21):**
  - **all per-value conversion in Rust** (`aiogram._core.ModelSchema` / `KindCore` in `crates/aiogram-core/src/conv/`):
    dict walker (`from_json`), one-pass JSON bytes (`load_json`, `jiter`), `to_json` / `dump`, and the flat codec
    (`from_flat` / `to_flat`). Rust-only: PyPy is dropped from 4.x (the `pypy-drop` PD), so there is no Python backend.
    `_converters.py` keeps the class-creation compiler, `register_converter`, `ConversionError` and the API;
  - `ModelConverter.from_flat` / `to_flat` / `load_json`, so F-09 and F-11 never loop over fields themselves;
  - the internal `RedisStorage._get_data_raw` hook for one-pass typed reads;
  - more kinds: `set` / `frozenset`, NamedTuple, TypedDict, smart `Union` with an optional `Discriminator`, a
    per-field `Converter` in `Annotated`;
  - the contract suite, run against the Python layer over the Rust core;
  - `make stubtest` (in `make lint`) for the hand-written `aiogram/_core.pyi`.

**Out:**
- The `FSMData` class and `FSMContext` API: [F-09](F-09-fsmdata-typed-fsmcontext.md).
- `CallbackData` itself: [F-11](F-11-callbackdata-without-pydantic.md) (gate-conditional).
- aiogram types as fields: [F-12](F-12-aiogram-types-in-fsmdata.md) (gate-conditional). The core must expose a hook
  for registering extra converters so F-12 can add them without changes here.
- Third-party model adapters: [F-10](F-10-pydantic-attrs-msgspec-adapters.md).

## Checklist

- [x] Decide `Fraction` support (**proposed default:** support `Fraction` in both codecs, encoded as `str(value)`
      (`"1/3"`) and decoded with `Fraction(text)`, because 3.x `CallbackData._encode_value` accepts it and dropping it
      would be an unlisted break; 11 §4's list omits it) — record in Notes and flag to owner.
- [x] Compiler + field specs; class-creation errors.
- [x] Converters for every type in Scope; flat-string subset enforced (non-flat types rejected for `to_str`).
- [x] Default/mutable-default/`exclude_unset` support.
- [x] Extension hook for extra converters (used by F-12), keyed by exact type, checked before the built-ins.
- [x] Contract suite (R16) and a micro-benchmark (A-05 harness): load of a 5-field flat class from JSON-shaped dict.
- [x] Tests (100% coverage of new code)

## Acceptance criteria

- The contract suite covers every type × codec × {valid, invalid} and passes.
- Unsupported annotations fail at class creation, not at first use.
- Loading a 5-field flat class (int, str, Enum, `int | None`, bool) from a dict ≤ 3 µs on the A-05 reference machine
  (3.x pydantic `CallbackData.unpack` is 2.9 µs; record the measured number in Notes).
- No import of pydantic, attrs or msgspec in the module (`python -X importtime` check in a test). The module needs
  `aiogram._core` by design (PD-35: Rust-only, PyPy is dropped) and imports it on first use, so importing the
  module stays stdlib-only.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep pydantic for validation | pydantic is no longer a dependency | D14 |
| Separate converters for CallbackData and FSMData | One table, flat subset vs JSON superset | D30, 04 §7 |
| Per-call reflection over annotations | Cost; table is built at class creation | 04 §7 |
| ~~Rust converters~~ | ~~User field conversion dominates; no gain~~ — revisited: all conversion runs in Rust (Rust-only, PyPy dropped), 2–4× faster than the pure-Python core | PD-35 |

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

- **Decide `Fraction` (default taken, flag to owner):** supported in both codecs, `str(value)` (`"1/3"`) and
  `Fraction(text)`, because 3.x `CallbackData._encode_value` accepts it.
- **Benchmark:** A-05 has not landed, so `scripts/bench_converters.py` stands in (A-05 method: warm-up, GC off,
  loops ≥ 0.2 s, median of 7); move it to `benchmarks/cases/fsm.py` with A-05. Measured 2026-11-18 on Apple M2 Pro,
  CPython 3.14.2: `from_json` of the 5-field flat class **1.45 µs**; 3.x pydantic `CallbackData.unpack` 3.81 µs in
  the same session (the 2.9 µs above is from another machine). No A-05 reference machine is defined yet.
- **API for F-09 / F-11 / F-12** (`aiogram/utils/_converters.py`):
  - `register_model(cls)` from `__init_subclass__` returns a `ModelConverter` with `fields` (tuple of
    `FieldSpec(name, converter, default, default_factory)`), `from_json`, `to_json`, `dump(obj, exclude_unset=)`
    and `init(instance, kwargs)` (the `__init__` body);
  - `converter_for(annotation)` returns a `Converter` (`flat`, `to_str`/`from_str`, `to_json`/`from_json`);
  - `model_converter(tp)` covers stdlib dataclasses too; `register_converter(tp, converter)` is the F-12 hook
    (exact type, checked before the built-ins, affects classes compiled afterwards);
  - errors: `ConversionError(ValueError)` with `.path`, `.value`, `.reason`. The set-fields record is the instance
    attribute `FIELDS_SET` (`"__fields_set__"`).
- **Semantics chosen here** (F-09 / F-11 may tighten them):
  - `to_json` is strict and is the validation step for Python values: an `int` field rejects `"1"` and `True`, and
    `Decimal` rejects `int`. `from_json` accepts JSON shapes: `float` also takes `int`, `list`/`tuple` take
    either, and `Decimal`/`UUID`/`Fraction`/`datetime`/`date` take `str` only. A `date` field rejects `datetime`.
  - `init` stores kwargs unconverted; whether the `FSMData` constructor validates is F-09's decision.
  - On load, unknown keys are ignored and keys present in the input count as set. `exclude_unset` applies at the
    top level only; a nested dataclass has no set record, so all its fields are dumped.
  - Registered models are built without `__init__` (they need an instance `__dict__`). Dataclasses are built with
    `cls(**values)`, so `__post_init__` runs, and a `ValueError` there becomes a `ConversionError`.
  - Mutable default = unhashable default (`[]`, `{}`, `set()`, non-frozen dataclass), deep-copied per instance.
    `dataclasses.field(default=/default_factory=)` is honoured on plain classes. Names starting with `_` and
    `ClassVar` fields are skipped.
  - Flat codec: `X | None` maps `None` to `""` and `""` to `None`. The 3.x rule for `str | None` with default `""`
    stays in F-11. UUID packs as hex (as in 3.x), bool packs as `"1"`/`"0"` and reads pydantic's lax set.
    `Literal` takes only `str`/`int`/`bool`/`None` values.
  - Rejected at class creation: unions other than `X | None`, `Any`, bare `list`/`dict`, fixed-length tuples,
    `set`, non-`str` dict keys, enums whose values are not JSON scalars (`str`/`int`/`float`/`bool`/`None`), and
    dataclasses with a required `InitVar` (loading cannot supply it).
  - A `Literal` or `Enum` whose values share a flat text (`1` and `"1"`, `True` and `1`) keeps its JSON codec but
    has no flat-string form, so it is rejected for callback data instead of changing values on a round trip.
  - `register_converter` matches the annotation as written, so `Annotated[float, "celsius"]` can be registered
    apart from `float`.
- **Forward references:** a name not yet defined when the class is created defers compilation to first use, where
  an unresolved name raises `NameError` (mutual recursion relies on this). A class defined in a function body under
  `from __future__ import annotations` that refers to another local class is deferred the same way, so its
  annotation errors surface on first use, not at creation. On Python 3.14+ an unquoted self-reference needs
  `get_type_hints(format=FORWARDREF)`; the default format raises `NameError` even with `localns`.
- The `-X importtime` test is skipped on PyPy, which ignores the flag.

- **PD-35 (briefs 04–08, 2026-11-21)** revises this plan: Rust now, Rust-only, raw-bytes path, more kinds, stubtest.
  - **Rust-only (brief 08).** PyPy is dropped from 4.x (the `pypy-drop` PD), so the converter has one backend. The
    first design (briefs 04–07) kept the Python code as the reference and PyPy backend, with Rust as a fast path that
    fell back to Python; it is replaced by a Python layer over Rust. Dropped with it: the Python per-value code,
    `_use_backend`, the PyPy guard, the differential Python-vs-Rust tests and the PyPy benchmark runs.
  - **The split.** Python compiles: annotation resolution, class-creation `TypeError`s, field specs, defaults, the
    converter objects with their tables and labels (`_by_json`, `_text`, `label`, union type sets, the discriminator
    tag table). Rust converts: every `from_json` / `to_json` / `from_str` / `to_str` / `dump` / `load_json`, and it
    builds the `ConversionError`s (reason, value, path) with the messages the Python code had. User converters
    (`register_converter`, a `Converter` in `Annotated`, a subclass of a built-in that does not declare its own
    `kind`) are Python objects the Rust core calls.
  - **Semantics changed with the rewrite:** `load_json` raises `ConversionError("invalid JSON: … at line L column
    C")` instead of `json.JSONDecodeError` / `UnicodeDecodeError`, and rejects an escaped lone surrogate (`json.loads`
    keeps it). When the one-pass walk meets a conversion error (or a value a repeated key overwrites), it parses the
    document once more and takes the `from_json` path, so results and errors are exactly the `from_json` ones; on
    invalid input user converters / `__post_init__` therefore run twice. Enums match by `(type, value)`, so
    `true` / `1.0` no longer load an `IntEnum`; `Flag` enums are rejected (composite values could not round-trip).
    `float` fields turn an overflow (`10 ** 1000`) into "expected a number". Set items that can be unhashable
    (through a union, `| None`, a non-frozen dataclass) are rejected at class creation. Nesting beyond 512 levels
    raises `RecursionError` instead of overflowing the native stack.
  - **Numbers** (M2 Pro, `scripts/bench_converters.py`, median µs, Rust / pydantic v2; the pure-Python core of this
    PR's first version in brackets):

    | Case | CPython 3.14.2 | 3.14t (no GIL) |
    |---|---|---|
    | a. callback unpack (`split` + `from_flat`) | 0.58 / 2.91 [1.24] | 0.66 / 3.05 |
    | b. 5 fields from dict | 0.41 / 0.62 [1.37] | 0.44 / 0.75 |
    | c. 5 fields from JSON | 0.65 / 0.71 [2.59] | 0.68 / 0.86 |
    | c′. + nested dataclass, JSON | 1.05 / 1.07 [3.77] | 1.08 / 1.27 |
    | d. 20 fields, JSON | 3.80 / 3.75 [12.42] | 4.17 / 4.17 |
    | d. 20 fields, dict | 2.15 / 2.68 [8.53] | 2.53 / 3.42 |
    | d′. 20 fields, 3 via Python converters, JSON | 4.50 / 3.83 [12.89] | 4.71 / 4.35 |

  - **Raw-bytes path (owner):** an internal hook on the built-in `RedisStorage` only; typed reads always parse the
    raw bytes and **bypass a custom `json_loads`**; Memory and Mongo storages use the dict walker. F-09 wires
    `FSMContext.get_data(tp)` to `_get_data_raw` + `load_json`.
  - **New kinds (owner + defaults):**
    - smart `Union` (owner): exact JSON / Python type first, then left to right; an optional
      `Annotated[A | B, Discriminator("kind")]` picks by a `Literal` tag field (owner answer read as "smart, plus an
      optional discriminator"); a tag shared by two members is rejected;
    - per-field converter (owner): a `Converter` instance in `Annotated` metadata, checked after an exact
      `register_converter` entry for the whole annotation and before the inner type;
    - constraints (owner): not added;
    - TypedDict (default): a plain `dict` of the declared keys present; `Required` / `NotRequired` honoured, also
      inside `Annotated` (the hint's wrapper wins over `__required_keys__`, which misses it under string
      annotations); unknown keys dropped; the dict is its own "set fields" record;
    - `set` / `frozenset` (default): a JSON list; NamedTuple (default): a JSON object built with `cls(**values)`;
    - flat codec (default): none of the new kinds has a flat form (F-11 rejects them at class creation through
      `.flat`), except a per-field converter whose `flat` is true.
  - **Compile under threads:** a model's / TypedDict's lazy field compile takes a per-converter `RLock`, so another
    thread waits instead of seeing a spurious "not ready"; a recursive reference in the same thread defers (the
    discriminator tag table of a recursive union is built on first use).
  - **Stubs (owner, after a probe):** `aiogram/_core.pyi` stays hand-written, as pydantic-core does; `make stubtest`
    runs in `make lint` (and so in CI's Lint job). PyO3 `experimental-inspect` + `maturin --generate-stubs` needs a
    declarative module, types `Bound<PyAny>` as `Any` and adds no imports; pyo3-stub-gen 0.23.3 adds 70 crates, pins
    `pyo3 < 0.31`, writes `_core/__init__.pyi` and drops `__version__`. aiogram_rust dropped pyo3-stub-gen for
    IR-emitted stubs.
  - **Layout (owner):** one `_core`; the converter is `src/conv/` (`errors`, `kind`, `compile`, `load`, `dump`,
    `json`, `flat`, `schema`). A separate `crates/aiogram-conv` rlib (scratch, measured on the dual-backend version,
    M2 Pro, sccache off): cold release ≈ 9.5 s in both, incremental release after touching a converter file 3.0 s vs
    4.2 s, dev 0.44 s vs 0.56 s, release binary byte-identical (657 328 B), codegen units 29 vs 16 with the largest
    60 KB vs 28 KB, µs rows equal within noise; `cargo test` needs libpython in both. Not better enough to switch.
  - The first compile of a model imports `aiogram._core`; `import aiogram` still does not (`test_build.py`).
