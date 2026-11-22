# B-14 — Decode runtime: unions, depth guard, response envelope, `getUpdates` batch

| Field | Value |
|---|---|
| Status | `done` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-03](B-03-decode-runtime.md) |
| Blocks | [B-04](B-04-spike-type-set.md), [B-09](B-09-sendmessage-encoder-response.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [C-19](../C-butcher/C-19-rust-forward-compat-emitter.md), [D-09](../D-client/D-09-response-decoder.md), [B-13](B-13-gate-run-and-decision.md) |
| Gate-conditional | no |
| Decisions | D10, D87 (depth), D107, R04, PD-03, PD-29 |
| Sources | [01-models.md §3.1](../../research/01-models.md), [05-network.md §2.2](../../research/05-network.md), [10-forward-compatibility.md §3 Layers 1–2](../../research/10-forward-compatibility.md), [13-aiogram-rust-review.md B7, B19, B22, B23](../../research/13-aiogram-rust-review.md), [07-free-threading.md §2](../../research/07-free-threading.md), [19 D107, R04, §3](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

On 3.x one bad update fails the whole `getUpdates` batch and polling retries the same offset forever (10 §1). The
gate's parse numbers (B24) are measured on the envelope and batch paths, not on single objects. B-03 builds the
decoder core (field tables, value kinds, sparse layout); this plan adds the parts that make decoding tolerant and
fast on real responses: union dispatch without a JSON tree (B23), the depth guard, the borrowed response envelope
(B22) and the per-update batch decode with byte copies (R04).

## Scope

**In** (inside `crates/aiogram-core`, next to B-03's `src/decode/`):
- **Unions (B23).**
  - A tagged union scans its object slice for the tag key while skipping values (`current_index` / `known_skip` /
    `slice_to_current`, verified on jiter 0.19.0), then decodes the chosen variant from the slice with a fresh
    `Jiter`.
  - An undiscriminated union uses a predicate hook (e.g. `date == 0`).
  - An unknown tag goes to the union's `Unknown` variant, which carries the common fields plus raw.
  - A **malformed member of a decoded union** becomes `Unknown` with a decode error and its raw range (D107).
- **Depth limit.** 128; deeper is a decode error. Stack guarded by re-entry with one `dyn` `stacker::grow` helper
  (B7, B19). Deep trees are dropped iteratively on 3.11.
- **Response envelope (B22).** `{"ok":true,"result":…}` borrows `result` as a raw slice and decodes in place;
  `{"ok":false,…}` returns `(error_code, description, parameters_raw)`.
- **`getUpdates` batch (10 Layer 2, R04, 19 §3.3).**
  - The result array is decoded element by element.
  - Each element's bytes are **copied** into its own `Arc<[u8]>`.
  - A failing element yields `(update_id, raw, DecodeError{path, message})`, with `update_id` extracted by a shallow
    scan even when the rest is invalid. The other elements are unaffected.
- **`Unknown…` decode hook:** one hook called at every `Unknown…` construction site (unknown tag, malformed member,
  unknown enum value, unknown update type): a process-wide first-occurrence counter per `(entity, field or tag)` (so
  the caller can log once, 10 §3) plus a strict-mode callback that turns the `Unknown` into an error. The hook only
  reports; the `DecodePolicy` switch that decides lenient vs strict stays with D-09 / E-14, and C-19's generated code
  calls the hook.
- **Per-update decode error** for batch / webhook bodies (the Python-facing class is defined in B-05).
- **Detach.** Batch and envelope decode run inside `py.detach` (no Python objects are touched during the Rust
  phase, 07 §2).
- `cargo test` coverage of everything above without Python, using A-04 fixtures read from disk.

**Out:**
- The decoder core: field tables, `Partial`, value kinds, sparse layout, error type (B-03).
- Concrete types and spike unions (B-04); Python wrappers / views and the Python decode-error class (B-05).
- Generated union code (C-19). `DecodePolicy` strict / lenient (D-09, E-14). `ClientDecodeError` wiring (D-02 / D-09,
  PD-29).

## Checklist

- [ ] Tagged-union tag peek and slice decode; predicate hook for undiscriminated unions; `Unknown` with common
  fields; malformed-member absorption (D107).
- [ ] Depth limit 128 with the re-entry stack guard; iterative drop. A test with a 10 000-deep `reply_to_message`
  chain must neither crash nor overflow.
- [ ] Response envelope (ok / error) and the `getUpdates` element-wise decode with per-update byte copy and
  shallow-scan `update_id`.
- [ ] Wrap the Rust-only phases in `py.detach`.
- [ ] `Unknown…` decode hook (first-occurrence counter + strict-mode callback), called at every `Unknown` construction
  site; `cargo test` that the counter fires once per `(entity, tag)` and the strict callback turns the second
  occurrence into an error.
- [ ] Tests: `cargo test` for every bullet in Scope, using A-04 fixtures, including an unknown tag
  (`update.unknown-tag`), a malformed union member (`update.malformed-member`), a missing required field outside a
  union (Layer 2) and depth 129 (`update.deep-nesting`).
- [ ] No changelog or registry entry (not wired, PD-03).

## Acceptance criteria

- The test from 10 §1, ported (a `getUpdates` batch where one element has an unknown union tag), decodes every
  element. The unknown one decodes to the `Unknown` variant, not an error.
- A batch where one element misses a required top-level field yields that element as a decode error carrying its
  `update_id` and raw bytes. The other 99 elements of A-04 case `response.getUpdates.100` decode.
- Decoding a retained element's data never references the batch buffer: drop the batch, keep one element, and check
  with `Arc::strong_count` plus an allocation test that the batch buffer is freed.
- Depth 128 decodes and depth 129 is an error; the 10 000-deep test passes on the CI stack size.
- `cargo clippy -D warnings` passes with the restriction lints (no `unwrap` / `expect` / `panic`).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| An intermediate JSON tree (serde_json `Value`) for unions or the envelope | Extra allocation and pass; jiter slice capture avoids it | 13 B22, B23 |
| Declaration-order fallback for undiscriminated unions | Dropped; tag or predicate, else `Unknown` | D107 (revises D85) |
| Slices into the shared `getUpdates` buffer | A retained child would pin a 100-update buffer | R04, 19 §3 item 3 |
| `grow(\|\| body)` stack guard | Compiles every body twice | 13 B19 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
```

## Workflow notes

- Inputs: B-03 (decoder core); A-04 fixtures (read by `cargo test` from the corpus path in the A-04 manifest).
- Outputs: union dispatch and the `Unknown…` decode hook for B-04's spike unions and C-19's generated ones; the depth guard C-18 emits calls to;
  envelope and batch entry points for B-09 and D-09.
- Can run in parallel with B-04's non-union types once B-03 lands.

## Notes
