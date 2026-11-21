# B-03 — Decode runtime core: field tables, value kinds, sparse layout

| Field | Value |
|---|---|
| Status | `done` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-01](B-01-crate-maturin-skeleton.md) |
| Blocks | [B-04](B-04-spike-type-set.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [B-13](B-13-gate-run-and-decision.md), [B-14](B-14-unions-envelope-batch-decode.md) |
| Gate-conditional | no |
| Decisions | D4, D10, D107, R04, PD-03, PD-29 |
| Sources | [01-models.md §3.1](../../research/01-models.md), [05-network.md §2.2](../../research/05-network.md), [10-forward-compatibility.md §3 Layers 1–2](../../research/10-forward-compatibility.md), [13-aiogram-rust-review.md B1, B7, B18, B20, B21](../../research/13-aiogram-rust-review.md), [08-build-release.md §7 items 12–16](../../research/08-build-release.md), [19 D107, R04, §3](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Parse (≥3×) and memory (≥4×) are mostly decided here. 3.x spends 84 µs and 42.5 KB on a realistic `Update`
(01 §1). The design is full, eager validation into Rust structs with no Python objects and no intermediate JSON tree
(01 §3.1). Only the Python wrappers are lazy (B-05). This task builds the **class-independent** decoder core that every
type uses. Per-type code is data plus trait impls (B-04), so C-18 can later emit it. Unions, the depth guard, the
response envelope and the `getUpdates` batch path build on this core in [B-14](B-14-unions-envelope-batch-decode.md).

## Scope

**In** (all inside `crates/aiogram-core`, layout suggestion `src/decode/`, `src/data/`):
- **Table-driven decoder (B1).** A per-type field table: wire name, accepted input aliases, kind, hot/cold, required.
  A `Partial` with `set_once` / `finish` behind a trait whose `Self` is the type (B18). Per-type bodies are
  `#[inline(never)]` and delegations `#[inline]`. Field values are bound to locals before building the struct (B20).
  No `#[derive(Deserialize)]`, no `#[serde(flatten)]`.
- **jiter integration.** Unknown keys are recorded as raw byte ranges into the owning update's buffer, not decoded.
  A per-field **present bitset** is kept per object (needed by `exclude_unset` aliases later, R06).
- **Value kinds.**
  - `i64` / `i32` / `f64` per schema format; bool.
  - Strings as `Box<str>`. Small enum-like strings interned in a process-wide Rust table.
  - Enums with an `Unknown(Box<str>)` variant (10 Layer 1).
  - Unix-time fields stored as `i64` (exposed as UTC `datetime` by B-05).
  - Arrays, nested objects, and an **opaque** kind (raw range, for B-04's out-of-set fields).
- **Sparse layout.** Hot fields inline as `Option<T>`; cold fields in `Option<Box<Cold>>`, or a sorted
  `(field_id, value)` vec for very wide types (Message).
- **Errors.** A Rust error type with a JSON path. Python mapping: `ValueError` for `from_json` / `from_dict`. The
  per-update decode error for batch/webhook is B-14's; the Python-facing classes are defined in B-05.
  `ClientDecodeError` wiring is D-02 / D-09 (PD-29).
- **`cargo test` coverage of everything above without Python.** Pure functions behind `#[cfg(test)]`, using A-04
  fixtures read from disk.

**Out:**
- Unions (tag peek, predicate, `Unknown`), the depth guard, the response envelope, the `getUpdates` batch with
  per-update byte copies, and `py.detach` (B-14).
- Concrete types (B-04) and Python wrappers / views (B-05).
- Encoder (B-09, D-07).
- Generated decode code (C-18 / C-19).
- `DecodePolicy` strict / lenient (D-09, E-14); the `Unknown…` decode hook (B-14). Logging of unknown tags (E-14 / H-01).

## Checklist

- [x] Field-table and `Partial` traits with `Self`-is-the-type placement (08 §7 item 13), plus `cargo llvm-lines` on
  a test type to confirm no generic instance per caller (item 12).
- [x] Value kinds, Rust-side interning table, enums with `Unknown`, present bitset, raw ranges for unknown keys.
- [x] Hot/cold sparse storage, both the boxed-cold variant and the sorted-vec variant.
- [x] Decide duplicate JSON keys inside one object (proposed default: last wins, as `json.loads` and 3.x pydantic
  do). Record in Notes and flag to owner.
- [x] Decide JSON strings with lone surrogates (`"\ud800"`), which Python `str` accepts but Rust `str` cannot hold
  (proposed default: the field becomes a decode error, isolated by B-14's nearest-union or per-update Layer 2 path,
  and the raw bytes stay available. Check the A-04 corpus for occurrences). Record and flag.
- [x] Decide input aliases (`from` / `from_user`, `bot` / `bot_user`, B17) (proposed default: accepted by
  `from_dict` / constructors only; wire decode (`from_json`, batch, webhook) accepts wire names only, since Telegram
  never sends Python names). Record and flag.
- [x] Tests: `cargo test` for every bullet in Scope, using A-04 fixtures: every value kind, unknown keys as raw ranges,
  the present bitset, both sparse variants, duplicate keys, a missing required field.
- [x] No changelog or registry entry (not wired, PD-03).

## Acceptance criteria

- A-04 case `update.realistic` decodes through the field tables into the sparse layout with every hot field inline and
  unknown keys kept as raw ranges (`cargo test`); `update.message.wide-sparse` uses the sorted-vec variant.
- A missing required field yields a Rust error carrying the JSON path of the field.
- `cargo llvm-lines` on the test type shows no generic instance per caller (08 §7 item 12).
- `cargo clippy -D warnings` passes with the restriction lints (no `unwrap` / `expect` / `panic`).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `#[derive(Deserialize)]` + `#[serde(flatten)]` | `flatten` buffers `Content`; table-driven is 1.35× faster and −196k macro lines | 13 B1 |
| Rust decode → pydantic `model_construct` | Pays both conversions | 01 §2 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
```

## Workflow notes

- Inputs: the B-01 crate; A-04 fixtures (read by `cargo test` from the corpus path in the A-04 manifest).
- Outputs: the decode traits and value kinds that B-14 builds on, B-04 implements per type and C-18 / C-19 emit.
- Can run in parallel with B-00 and B-02.

## Notes

- **Layout.** `crates/aiogram-core/src/decode/` (`cursor.rs` shared walker, `table.rs` field tables, `value.rs` value
  kinds and storage, `error.rs`), private, no Python surface, not wired (PD-03). A type implements `Decode`
  (`TABLE`, `Partial`, `Bits`, `set`, `finish`); the object loop is the trait's own `#[inline(never)] decode`, key
  lookup, unknown keys and present bits are the one non-generic `Cursor::field`. The test types in
  `decode/tests/types.rs` show the shape B-04 writes and C-18 emits (Message: all 130 fields, sorted cold vec).
- **`cargo llvm-lines`** (`--lib --profile test`): every decode function has exactly one copy; `decode` is one per
  type, `Cursor::opt` / `Cursor::list` one per value type, `Cursor::field` one in total.
- **Duplicate keys (Decide, proposed default taken; flagged).** Last wins, as `json.loads` and 3.x pydantic do,
  `null` included (`{"a":1,"a":null}` leaves `a` unset-to-`None` with its present bit set). Every occurrence of a
  duplicate unknown key is kept as a range, in input order.
- **Lone surrogates (Decide, proposed default taken; flagged).** A lone `\udXXX` escape is a decode error at the
  nearest known field, with the byte offset. jiter rejects it in skipped values too (unknown keys, opaque fields),
  not only in decoded strings, so "the raw bytes stay available" holds for the update's buffer, not for the
  object. None of the 22 corpus payloads has one; B-14 isolates the error per union member or update.
- **Input aliases (owner, 2026-11-21).** Both names (wire and Python: `from` / `from_user`, `bot` / `bot_user`) are
  accepted on every input path, as 01, 13 B17 and C-18 say: one sorted `keys` table maps both to one field id, last
  wins when both are sent. Errors name the wire field.
- **Intern table (owner).** Static and sorted, no runtime growth, no lock; the seed list is provisional until C-18
  generates it. **`ValueError` (owner):** `From<DecodeError> for PyErr` lives here.
- **`null`** for an optional field is `None` with the present bit set (pydantic's `exclude_unset` keeps it); for a
  required one it is the missing-field error.
