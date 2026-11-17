# C-18 — Rust type emitter (data, decode tables, views)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-09](C-09-resolution-passes.md), [B-04](../B-spike/B-04-spike-type-set.md), [B-05](../B-spike/B-05-views-cache-gc-routing-keys.md), [B-06](../B-spike/B-06-value-semantics-native-api.md), [B-07](../B-spike/B-07-bound-views.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [B-03](../B-spike/B-03-decode-runtime.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md), [B-14](../B-spike/B-14-unions-envelope-batch-decode.md) |
| Blocks | [C-19](C-19-rust-forward-compat-emitter.md), [C-20](C-20-rust-methods-shortcuts-emitter.md), [C-21](C-21-generated-tests-emitter.md), [C-27](C-27-port-ext-helpers.md), [D-09](../D-client/D-09-response-decoder.md), [I-06](../I-distribution/I-06-largest-codegen-unit-guard.md), [H-12](../H-testing-observability/H-12-toolkit-model-api-migration.md), [I-02](../I-distribution/I-02-tier1-wheel-matrix-release.md) |
| Gate-conditional | yes |
| Decisions | D4, D83, D84, D87, D102, D103, D106, D108, D109, 19 §8 (text_signature), PD-30 |
| Sources | [01-models.md §3.1–3.7](../../research/01-models.md), [02-butcher.md §5, §5.2 emitter rules](../../research/02-butcher.md), [08-build-release.md §5, §7 items 6, 11–16](../../research/08-build-release.md), [13-aiogram-rust-review.md B1–B3, B7, B11, B18–B21](../../research/13-aiogram-rust-review.md), [19 §2 R03, R04, §8](../../research/19-review-resolutions.md), [plans README PD-30](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The B spike hand-writes about 12 types (incl. the wide `Message`) **in emitted shape** (PD-30). This task generates all
of them from the IR. Its first acceptance test is a **golden diff**: the emitter reproduces B-04's hand-written spike
types with no semantic differences, and then extends to every type. The emitter must follow the codegen rules learned
from aiogram_rust, because what made their build slow was *where* code landed, not how much of it there was (13 §7).

## Scope

**In:** `crates/butcher/src/emit/rust.rs` → `crates/aiogram-core/src/generated/types/**`:
- **Data structs** per type, using the field split from `layout.toml`:
  - hot fields inline `Option<T>`;
  - cold fields in `Option<Box<Cold>>`, or a sorted `(field_id, value)` vec for very wide types (`Message`);
  - int widths from the IR (`i64`/`i32`/`f64`); datetime as `i64`; strings as `Box<str>`/`Arc<str>`;
  - enums referenced as Rust enums with `Unknown(Box<str>)` (C-19 emits the enums);
  - collections stored so that views return cached tuples (D106);
  - display fields marked lazy in `display.toml` (C-06 kind 12) store a lazy object **unchanged** (frozen-safe, D15);
    only the encoder renders it (D-10 / G-06).
- **Table-driven decode** (B1): a per-type field table plus `Partial` with `set_once` / `finish`; no
  `#[derive(Deserialize)]`, no `#[serde(flatten)]`. Unknown keys are kept as raw slices. On input, both wire and Python
  names are accepted (`from`/`from_user`, `bot`/`bot_user`; D109, B17).
- **Views:** `#[pyclass(frozen, module = "aiogram.types")]` wrappers, wired to B-05's wrapper cache (slots only for
  present non-scalar fields, R04) and B-07's bound views (D103). Getters return Python names.
- **Base surface through the per-type vtable** (B3): `to_json` / `to_dict` / `from_*` / `replace` / eq / hash / repr /
  pickle live once on the base. The generated code is data (field tables), not methods.
- **Deprecated `model_*` aliases** (D91, 19 §2 R06 alias contract) on the same base: `model_dump`, `model_dump_json`
  (returns `str`, wire names, D94), `model_validate`, `model_validate_json`, `model_copy(update=)` → `replace`,
  `model_extra` (unknown fields only, `{}` when none), `model_dump(exclude_unset=True)` via the present bitset. Each
  warns through I-12's `warn_deprecated` with its registry id. `model_fields` is not provided (D95). Owner of the
  aliases by coordinator decision (B-06 lists them as out of scope).
- **Constructors:** `(**kwargs)` → `from_dict` internally (08 §7 item 11), with a generated **`text_signature`** that is
  keyword-only and uses `...` for every nonliteral default (`inspect` rejects `Default('parse_mode')`, 19 §8). Stubs carry the real defaults (C-14).
- **Secondary bases** (D83): `SecondaryBase.register(Type)` emitted in the Python `__init__` (C-13 hook), and the
  secondary bases' members generated on the type.
- **Codegen rules:**
  - field values bound to locals before building structs (B20);
  - per-class shared code as trait methods with `Self` = the class, `#[inline(never)]` bodies and `#[inline]` delegations (B18);
  - class-independent code hoisted into shared non-generic helpers (B21);
  - depth guard by re-entry (B19), via the hand-written runtime from B-14;
  - clippy restriction lints stay denied in generated code (B11);
  - `prettyplease` formatting.
- `freelist` for small high-churn types (`MessageEntity`, `PhotoSize`, `User`) per 08 §7 item 6, configured in `layout.toml`.

**Out:**
- unions, `Unknown…` variants, enums, `Update.event_type` (C-19);
- methods, shortcuts and encoders (C-20);
- generated tests (C-21);
- the hand-written decode runtime, wrapper cache and bound views (B-03, B-14, B-05, B-07);
- the largest-unit CI guard (I-06).

## Checklist

- [ ] Emitter for data structs, field tables, `Partial`, views and `text_signature`.
- [ ] Lazy display fields (`display.toml`) stored unchanged; test that a stub lazy object passed as
  `InlineKeyboardButton(text=...)` is returned by identity from the getter.
- [ ] **Golden diff** (PD-30): emit B-04's spike type set and diff it against B-04's hand-written files. Allowed
  differences are formatting and ordering only; anything else is listed and fixed in either the emitter or (with B's
  owner) the spike code.
- [ ] Replace B-05's D105 spike shim (local `warnings.warn(..., DeprecationWarning)`) with I-12's `warn_once` +
  `AiogramDeprecationWarning`, still once per `(type, name)`; test that the shim is gone and the warning class is
  I-12's.
- [ ] `model_*` alias set on the base surface, one test per alias (behaviour + one deprecation warning each).
- [ ] Full emission for all IR types; `cargo build --release` of `aiogram-core` succeeds.
- [ ] `inspect.signature(T)` works for every type (no `ValueError`) and shows keyword-only params (generated test hook, C-21).
- [ ] Record the release build time, binary size and largest codegen unit (`-C save-temps`) in Notes, as the baseline for I-06.
- [ ] Migration-registry entry (PD-13): verify the A-11 seed covers breaking changes 1, 2, 3, 19, 22 and 23 (pydantic base, immutability, subclass registration, JSON-shaped extras, `as_` new view, tuples); add the missing ones. Changelog fragment.
- [ ] Tests (100% coverage of new Python; `cargo test` for decode on fixture JSON)

## Acceptance criteria

- The golden diff against B-04's spike types has 0 semantic differences.
- A-08's model oracle decode cases pass (manifested differences only, R26) on the full generated set.
- `cargo clippy -D warnings` passes with the restriction lints on generated code.
- A lazy object in a `display.toml` field is stored and returned unchanged (`is` identity), and no render happens at
  construction.
- B-13's gate numbers do not regress by more than 5% when the hand-written spike types are swapped for the generated ones (same pinned inputs as B-02/B-13).
- The release build's largest codegen unit is ≤ 2× the median (the initial I-06 threshold, to be calibrated there).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `#[derive(Deserialize)]` + `serde(flatten)` | 1.35× slower, +196k macro lines | 13 B1 |
| Eager materialisation of every nested object | Memory target; laziness gives identity and O(1) re-mount | D4, 13 §4 |
| Multi-crate layout | One crate with placement rules | D102 |
| Prototype butcher during the spike | Spike types hand-written in emitted shape | PD-30 (revises 01 §5.1) |
| Per-class generic `fn f<T>` | Lands in the defining module's codegen unit | 13 B18 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test -p aiogram-core
cargo xtask butcher emit && maturin develop --release
uv run pytest tests
uv run mypy aiogram
cargo xtask butcher check
```

## Workflow notes

- Starts only after B-13 is *go*. Inputs: the B-04 types (golden), and the runtime APIs of B-03/B-14/B-05/B-06/B-07 (decode
  runtime core, unions/depth guard/envelope, wrapper cache, native API, bound views).
- C-19 and C-20 extend this emitter. D-09 (response decoder) uses the generated types.

## Notes
