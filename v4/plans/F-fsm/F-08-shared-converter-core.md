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
- Modules (plan-10): the public, stdlib-only `aiogram/utils/converters.py` (declarations) and the private
  `aiogram/utils/_converters.py` (resolver, `ModelBase`, schemas):
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
- **Added by PD-36 (owner, 2026-11-21):**
  - **all per-value conversion in Rust** (`aiogram._core.ModelSchema` / `KindCore` in `crates/aiogram-core/src/conv/`):
    dict walker (`from_json`), one-pass JSON bytes (`load_json`, `jiter`), `to_json` / `dump`, and the flat codec
    (`from_flat` / `to_flat`). Rust-only: PyPy is dropped from 4.x (PD-35), so there is no Python backend.
    `_converters.py` keeps the class-creation compiler, `register_converter`, `ConversionError` and the API
    (revised by plan-10, see Notes);
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
- [x] Extension hook for extra converters (used by F-12): a type's own `__aiogram_converter__` classmethod, found
      along the MRO, checked before the built-ins (plan-10; the global exact-type `register_converter` is gone).
- [x] Contract suite (R16) and a micro-benchmark (A-05 harness): load of a 5-field flat class from JSON-shaped dict.
- [x] Tests (100% coverage of new code)

## Acceptance criteria

- The contract suite covers every type × codec × {valid, invalid} and passes.
- Unsupported annotations fail at class creation, not at first use.
- Loading a 5-field flat class (int, str, Enum, `int | None`, bool) from a dict ≤ 3 µs on the A-05 reference machine
  (3.x pydantic `CallbackData.unpack` is 2.9 µs; record the measured number in Notes).
- No import of pydantic, attrs or msgspec in the module (`python -X importtime` check in a test). `_converters.py`
  imports `aiogram._core` at the top (PD-36, plan-10); `import aiogram` imports neither it nor `_core`, and the public
  `aiogram.utils.converters` stays stdlib-only (`tests/test_core/test_build.py`).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep pydantic for validation | pydantic is no longer a dependency | D14 |
| Separate converters for CallbackData and FSMData | One shared annotation resolver; separate JSON and flat *schemas* on top of it (plan-10 revises "one table") | D30, 04 §7, PD-36 |
| Per-call reflection over annotations | Cost; table is built at class creation | 04 §7 |
| ~~Rust converters~~ | ~~User field conversion dominates; no gain~~ — revisited: all conversion runs in Rust (Rust-only, PyPy dropped by PD-35), 2–4× faster than the pure-Python core | PD-36 |

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
- **API and semantics:** see "Plan-10 redesign" below. The `register_model` / `ModelConverter` / `converter_for` /
  `register_converter` API, the `FIELDS_SET` attribute and the "rejected at class creation" list of the first versions
  are gone.
- **PD-36 (briefs 04–08, 2026-11-21)** revises this plan: Rust now, Rust-only, raw-bytes path, more kinds, stubtest.
  - **Rust-only (brief 08).** PyPy is dropped from 4.x (PD-35), so the converter has one backend. The
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

- **Plan-10 redesign (briefs 10–11, owner 2026-11-21; PD-36).** It replaces the briefs 04–09 API above.
  - **Declaration.** `ModelBase`, the base that F-09 / F-11 subclass:
    - `@dataclass_transform(kw_only_default=True, field_specifiers=(field, dataclasses.field))`, with a typed
      `__init_subclass__(*, rename=, converters=, frozen=, slots=)`;
    - the runtime follows PEP 681: `_x` names are fields; `field(init=False / kw_only=False / default_factory / repr
      / compare)` and the aiogram sugar `key=` / `load=` / `converter=`; inherited fields come first; `ClassVar` is
      skipped; `KW_ONLY` / `InitVar` are a `TypeError`;
    - the constructor checks every value (`ConversionError`) and raises dataclasses-style `TypeError`s;
    - `__post_init__` runs after construction and after every load;
    - frozen models hash their fields;
    - `copy.replace`, pickle and copy work; there is no dataclasses API (`is_dataclass`, `asdict`);
    - `fields_set(obj)` reads the `__fields_set__` slot;
    - mypy and pyright both check a `rename=` / `frozen=True` / `slots=True` model correctly
      (`tests/typing/test_converters.py`).
  - **`slots=True`** goes through a metaclass on `ModelBase`: `__init_subclass__` runs after the instance layout is
    fixed, so the metaclass moves the defaults out of the namespace and declares the slots. A user `__slots__` model
    works as well. Every model is built through `PyObject_GenericSetAttr`.
  - **No global registry.**
    - The schema lives on the class (`__aiogram_core__`, `__aiogram_json__`, `__aiogram_flat__`).
    - Lookup order: `Annotated[T, Conv]` > the class map `converters={type: Conv}` (exact type, then along the MRO
      except through the built-in scalars) > the type's `__aiogram_converter__` hook > the built-ins.
    - The class map reaches into containers and into foreign dataclasses / NamedTuples / TypedDicts, but not into
      another `ModelBase`; subclasses inherit it.
  - **One resolver, two schemas.**
    - `json_schema(cls)`: `load`, `load_json`, `dump`, `dump_json`, `dump_fields`, `keys`.
    - `flat_schema(cls)`: positional `load` / `dump`, `TypeError` for a non-flat field, a `Key` or `rename`.
    - `json_codec(annotation)`: any annotation, including its flat form.
    - The Python→Rust interface is the typed constructors in `conv/ir.rs` and `_core.pyi`. Rust reads no resolver
      attribute by name.
  - **Errors.**
    - One `ConversionError(ValueError)` with `.errors`, a list of `ErrorDetail(loc, message, value)`, and `.title`
      (`loading Form`, `dumping Form`, `constructing Form`). `str()` always starts with the header line
      (`2 errors loading Form`); `repr` carries the errors.
    - The JSON codec collects every error, up to 100. Unions and the flat codec stop at the first.
    - Union member reasons become notes. A user `ValueError` becomes a line at its path, with the exception as
      `__cause__`.
    - Rust keeps error lines and builds the exception once at the boundary, so a union miss costs no Python object.
  - **Keys.**
    - `rename="camel" | "snake" | "kebab" | callable`, and `Annotated[T, Key("x", load=("old",))]`.
    - On load the stored key wins over the `load` keys, whatever their order in the document.
    - Error locations use stored keys. `JsonSchema.keys` gives F-09 the old keys to delete on write.
  - **Bytes.**
    - `load_json` is one pass with no re-parse, so user code runs once. A repeated key: the last one wins, and the
      overwritten value's converter has also run.
    - The input is validated as UTF-8 up front. A BOM is skipped for bytes only.
    - `dump_json` writes compact JSON: floats as `repr`, strings as `json.dumps(ensure_ascii=False)` writes them,
      NaN / Infinity as `json.dumps` writes them.
    - `RedisStorage._raw_reads` / `_raw_writes` (stdlib `json_loads` / `json_dumps`) gate `_get_data_raw` /
      `_set_data_raw`, which F-09 wires.
  - **Native kinds.**
    - UUID, `datetime` / `date` / `time` (Rust parse fast path, `fromisoformat` fallback, exact `isoformat` output),
      `timedelta` (a number of seconds), Decimal (text, or an exact JSON number on the bytes paths with
      `DecimalAsNumber`: a lossy float on the dict path), bytes (padded base64 in JSON, unpadded base64url flat).
    - The ready-made `IsoDatetime(timespec, sep)`, `EpochDatetime(unit)`, `DecimalAsNumber`, `EnumByName` and
      `UuidHex` select a native format, with no Python call per value.
    - NewType and PEP 695 aliases unwrap: generic ones are substituted, recursive ones become lazy kinds.
    - Fixed `tuple[A, B]` is supported. `dict` keys must be `str`.
  - **Forward references.**
    - Each field is evaluated in the namespace of its declaring class, in this order: the class, class-body types
      that are not field names, the defining function's frame locals (kept until the class resolves), the module.
    - `date: date = date(...)` works, also on 3.14 without `__future__`.
    - A bad field is a `TypeError` at class creation, even next to a pending one.
    - A class that cannot resolve raises `NameError("X is not fully defined: Y is not defined")` on first use.
      `CallbackQueryFilter` does not swallow it.
  - **Numbers.** M2 Pro, `scripts/bench_converters.py`, median µs. The release build of this code, the release build
    of `6045e6d1` (from `git archive`) and pydantic v2 were run back to back in one session; the machine was slower
    that day than for the table above, so compare within a row:

    | Case | 3.14.2: new / `6045e6d1` / pydantic | 3.14t (no GIL): new / pydantic |
    |---|---|---|
    | a. callback unpack | 0.59 / 0.59 / 3.02 | 0.65 / 2.98 |
    | b. 5 fields, dict | 0.40 / 0.41 / 0.63 | 0.45 / 0.75 |
    | c. 5 fields, JSON | 0.48 / 0.68 / 0.73 | 0.52 / 0.82 |
    | c′. + nested dataclass, JSON | 0.89 / 1.07 / 1.11 | 0.90 / 1.27 |
    | d. 20 fields, JSON | 3.25 / 3.80 / 3.54 | 3.44 / 4.18 |
    | d. 20 fields, dict | 1.80 / 2.10 / 2.61 | 2.16 / 3.45 |
    | d′. with datetime / UUID / Decimal, JSON | 3.39 / 4.45 / 3.87 | 3.64 / 4.43 |
    | d′. same, dict | 2.00 / 2.69 / 2.80 | 2.38 / 3.71 |
    | e. UUID ×100, load / dump | 11.95 / 49.28; 9.85 / 31.61 | 13.41; 10.35 |
    | e. datetime ×100, load / dump | 4.76 / 4.89; 14.30 / 63.97 | 5.34; 14.56 |
    | e. Decimal ×100, load / dump | 8.64 / 8.65; 5.18 / 5.75 | 10.05; 5.17 |
    | f. `list[UUID \| str]`, 100 misses | 21.07 / 80.60 | 22.44 |
    | g. invalid `load_json` (3 errors) | 6.05 / 3.79 | 5.93 |
    | h. `dump` of d′ | 1.73 / 2.39 / 3.03 | 2.00 / 3.95 |
    | h. `dump` + `json.dumps` | 5.58 / 6.36 | 5.74 |
    | h. `dump_json` | 2.11 / — / 3.01 | 2.33 / 3.61 |
    | i. the validating constructor (5 fields) | 0.57 / — / 0.53 | 0.65 / 0.65 |

    UUID loads and dumps are 3–4× faster, datetime dumps 4.5× faster; `datetime` and `Decimal` loads already used
    the C constructors and stay level. `dump_json` costs a third of `dump` + `json.dumps`. Row g is slower because
    the load now collects every error (one pass); the old core stopped at the first one and re-parsed.
  - **Known limits:**
    - jiter's 200-level limit on skipped or materialised values raises `RecursionError`.
    - `load_json` of an escaped lone surrogate re-parses through `json.loads`, the only re-parse left.
    - Flat form: `str | None` packs `None` as `""`, so `""` unpacks as `None` (3.x `CallbackData` behaved the same;
      F-11 owns the #2007 empty-part rule). `bytes | None`, and an enum or `Literal` with a `""` text, have no flat
      form under `| None`. A flat user converter whose `to_str` returns `""` under `| None` has the `str` behaviour.
    - `type X = X | int` (a self-reference outside a container) is a `TypeError` at class creation.
