# C-14 — `.pyi` stub emitter

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-09](C-09-resolution-passes.md), [C-10](C-10-ledger-diff.md), [C-13](C-13-reexport-modules.md), [B-06](../B-spike/B-06-value-semantics-native-api.md), [B-10](../B-spike/B-10-ext-helpers-stub-workflow.md) |
| Blocks | [I-04](../I-distribution/I-04-installed-wheel-typing-stubtest.md), [I-09](../I-distribution/I-09-import-free-docs-build.md), [I-17](../I-distribution/I-17-model-semantics-rules.md), [G-06](../G-features/G-06-lazy-text-capture.md), [G-11](../G-features/G-11-generated-utils-signatures.md) |
| Gate-conditional | yes (the type base surface follows D91–D95, D103, D106) |
| Decisions | D100, D10, D107, D106, D109, D79, D11, D91–D95, D105, D18, PD-02, PD-23 |
| Sources | [02-butcher.md §5.1, §5.2](../../research/02-butcher.md), [01-models.md §3](../../research/01-models.md), [10-forward-compatibility.md §3](../../research/10-forward-compatibility.md), [18-docs-migration.md D79](../../research/18-docs-migration.md), [19 §2 R29, §8](../../research/19-review-resolutions.md), [plans README PD-23](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

With Rust pyclasses, the stubs are the whole typed API, and the API reference comes from them: sphinx-autoapi over
`*.pyi`, which win over the thin `.py` files (D79, R29). Today 575 `TYPE_CHECKING` `__init__` blocks fake this for
pydantic; they are removed (11 §1). PyO3's stub generation is experimental and not used (02 §5.1). aiogram_rust's stubs
were missing 203 members until they were checked (13 B10).

## Scope

**In:** `crates/butcher/src/emit/pyi.rs`, writing `aiogram/types/<x>.pyi`, `aiogram/methods/<x>.pyi`, and
`aiogram/client/_bot_methods.pyi` if C-15 needs it:
- **Types:**
  - class with its primary base, Python field names (D109 renames, `from_user`) as read-only properties;
  - collection fields as `tuple[X, ...]` (D106); datetime fields as `datetime.datetime`; enum fields as `ChatType | str` (10 Layer 1);
  - keyword-only `__init__(self, *, …)` with real `Default(...)` values (D100);
  - **no `**extra`** (PD-23: D99/D87 unknown kwargs are runtime-only and documented);
  - D18-merged twins as one class;
  - display fields marked lazy in `display.toml` (C-06 kind 12) typed `str | LazyText` (constructor parameter and
    property), so lazy text type-checks (G-06). `LazyText` is imported from `aiogram/_lazy.py`, a tiny engine-free
    public module this plan creates: a `typing.Protocol` with
    `__aiogram_render__(ctx) -> tuple[str, tuple[MessageEntity, ...] | None]` (the G-03 contract), no imports beyond
    `typing`. G-03 implements `L` / `LazyProxy` against it and re-exports it from `aiogram.i18n`.
- **Unions:** a type alias including `Unknown<Union>` **only for decoded unions** (D107), plus the `Unknown<Union>`
  class with the common fields, `tag`, `raw` and `decode_error`.
- **Base surface** (from B-06's native API): `to_json() -> bytes`, `to_dict()`, `from_json`, `from_dict(…, *, bot=None)`,
  `replace(**changes)`, `__replace__`, `as_(bot) -> Self` (D103), `raw`, `raw_json`, `bot`, and the deprecated `model_*`
  aliases with `@deprecated` (D91, D94). No `model_fields` (D95).
- **Methods:** keyword-only `__init__`, `__returning__`-equivalent typing for `await bot(method)`.
- **Shortcuts** from the C-07 resolved table: keyword-only, with the target method's params minus the filled ones.
- **Ledger deprecations** (C-10): `@deprecated` (typing_extensions) and a `.. deprecated::` docstring note.
- **`*_ext.pyi` fragments** (B-10 workflow): merged into the generated stub, with C-09's collision check covering names.
- Docstrings from IR `Doc` in RST for autoapi; imports computed from the IR (no F821 class of bugs).
- `ruff format` on the output.

**Out:** `.py` re-exports (C-13), `_BotMethods` (C-15), stubtest and installed-wheel typing CI (I-04), docs build (I-09).

## Checklist

- [ ] Type, union, method and shortcut stub templates (minijinja).
- [ ] Import computation per file from IR references.
- [ ] Ext-fragment merge.
- [ ] Create `aiogram/_lazy.py` with the `LazyText` Protocol (engine-free; importing it imports no i18n engine).
- [ ] `str | LazyText` for every `display.toml` field, imported from `aiogram._lazy`; `assert_type` case for
  `InlineKeyboardButton(text=<a minimal class implementing LazyText>)`.
- [ ] Deprecation rendering from the ledger.
- [ ] Remove the `TYPE_CHECKING` `__init__` stubs and the `model_rebuild` / `_types_namespace` tail of `aiogram/types/__init__.py` from the 4.x tree (11 §1); PD-03 staging applies until B-13 is a go.
- [ ] mypy test file (`tests/typing/test_stubs.py` (directory from B-01; create if absent), run by mypy) with `assert_type` cases: a keyword-only constructor, positional call rejected, tuple field, `Unknown…` in a decoded union and absent from `ChatId`, enum `| str`, the `bot_user` rename, `@deprecated` on a fixture ledger entry, an unknown kwarg rejected by mypy (PD-23).
- [ ] Migration-registry entry (PD-13): verify A-11 seeds `removal-4.0` entries for keyword-only (D100, breaking change 21), tuples (D106, 23) and `model_fields` (D95); add any that are missing. Changelog fragment.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `uv run mypy aiogram tests/typing` passes on a dev build with the emitted stubs.
- `stubtest aiogram._core aiogram.types aiogram.methods` reports 0 missing members (run here once; I-04 adds the CI job).
- No emitted stub exceeds 2.5 MB (PyCharm limit), and the largest file is reported.
- Two runs emit byte-identical stubs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| PyO3 / pyo3-stub-gen stub generation | Experimental; aiogram_rust dropped it (12 min → 7.3 s from IR) | 02 §5.1, 13 §2 |
| `**extra: Any` on constructors | Hides typos from type checkers | PD-23 |
| `Unknown` on request-only unions | Never decoded | D107 |
| One merged stub file | Size limit, reviewability | D16 |

## Validation

```bash
cargo clippy --all-targets -- -D warnings
cargo test -p butcher emit_pyi
cargo xtask butcher emit && make dev
uv run mypy aiogram tests/typing
uv run python -m mypy.stubtest aiogram.types aiogram.methods
uv run pytest tests
cargo xtask butcher check
```

## Workflow notes

- The base surface follows B-06 (native API) and B-10 (ext fragment format). If they change, update the templates, not the IR.
- I-04 adds stubtest and installed-wheel `assert_type` to CI. I-09 builds autoapi docs from these stubs. I-17 (model-semantics checker rules) reads the same surface.

## Notes

- Coordinator default (reconciliation): this plan owns the engine-free `aiogram/_lazy.py` (`LazyText` Protocol); G-03
  implements it and re-exports it from `aiogram.i18n`.
