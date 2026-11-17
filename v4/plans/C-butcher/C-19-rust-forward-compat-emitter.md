# C-19 — Rust forward-compat emitter: unions, `Unknown…`, enums, `Update.event_type`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-18](C-18-rust-type-emitter.md), [B-04](../B-spike/B-04-spike-type-set.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [B-14](../B-spike/B-14-unions-envelope-batch-decode.md) |
| Blocks | [C-21](C-21-generated-tests-emitter.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md), [D-09](../D-client/D-09-response-decoder.md), [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md), [E-09](../E-runtime/E-09-routing-keys-compiled-rejectors.md) |
| Gate-conditional | yes |
| Decisions | D10, D85, D107, D105, D108, R07 |
| Sources | [10-forward-compatibility.md §3](../../research/10-forward-compatibility.md), [01-models.md §3.1, §3.6](../../research/01-models.md), [19 D107](../../research/19-review-resolutions.md), [11-removals.md §1](../../research/11-removals.md), [13-aiogram-rust-review.md B22, B23](../../research/13-aiogram-rust-review.md), `aiogram/types/update.py` (3.x `event_type`, `UpdateTypeLookupError`) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

On 3.x, an unknown union tag (e.g. `ChatMember.status = "superadmin"`) fails the **whole `getUpdates` batch**, and
polling retries the same offset forever. An unknown update type makes `Update.event_type` raise
`UpdateTypeLookupError` (10 §1). D10 / D107 make expected API evolution never fail. This task generates that tolerance
for every decoded union and enum.

## Scope

**In:** `crates/butcher/src/emit/rust_unions.rs` (+ enum emission):
- **Decoded unions** (C-09 classification):
  - discriminated: peek the tag on the raw slice and decode the chosen variant from the slice (B22/B23, jiter
    `known_skip` + `slice_to_current`, via the B-14 runtime);
  - undiscriminated: overlay tag or predicate (e.g. `date == 0` → `InaccessibleMessage`), with no declaration-order fallback (D107);
  - otherwise `Unknown<Union>`, carrying `tag`, the variants' common fields (C-09), `raw` and `decode_error`.
- **Malformed members** (D107): a malformed member of a decoded union becomes `Unknown…` with `.decode_error` and its
  raw value. Failures outside any union propagate to the per-update `UpdateDecodeError` (B-14 / E-14).
- **`ChatMemberAdapter` replacement:** the 3.x `aiogram/utils/chat_member.py` (`ChatMemberAdapter`, a pydantic
  `TypeAdapter` over the `ChatMember*` union) is replaced by the generated `ChatMember` union decoder. Whether the
  public module is kept is a Decide item below (proposed: remove).
- **Routing content-kind table (owned here):** the Rust content-kind table behind `Update.routing_keys()` (overlay
  `content.toml` kind 14), emitted together with `Update.event_type`. It replaces B-05's hand-written spike table; the
  Python `aiogram/_generated/content_kinds.py` (C-16) serves only E-05 / H-11.
- **Request-only unions** (`ChatId`, `InputFile`, `DateTime`, …): no `Unknown` (D107).
- **Enums:** Rust enums with `Unknown(Box<str>)`. Getters return `str` (3.x `use_enum_values` contract). Small values are interned.
- **`Update.event_type` / `event` / `__hash__`**, generated from the `Update` fields:
  - an unknown key gives `event_type` = that key and `event` = `UnknownEvent(type, raw)`;
  - no `lru_cache` on `self` (11 §1);
  - first occurrence per `(entity, field or tag)` logs one `WARNING` on `aiogram.event`, as specified in 10 §3; the first-occurrence counter comes from B-14's `Unknown…` decode hook.
- **`DecodePolicy` "strict"** turns any `Unknown` or decode error into an exception. The switch lives in D-09 / E-14;
  the hook (counter + strict callback) is B-14's; this emitter calls it at each `Unknown` construction site.

**Out:** per-update isolation in polling and webhook (E-14, E-15, E-16); the `router.unknown_update` observer (E-05);
the D105 attribute fallback (B-06).

## Checklist

- [ ] Union decode emitter (discriminated / predicate / `Unknown`).
- [ ] `Unknown<Union>` classes with common fields, `tag`, `raw`, `decode_error`.
- [ ] Enum emitter with `Unknown(Box<str>)` and interning.
- [ ] `Update.event_type` / `event` / `__hash__` emitter (Rust side of the C-16 Decide item).
- [ ] Strict-policy hook at every `Unknown` site.
- [ ] Decide keep-or-remove of the public `aiogram/utils/chat_member.py` module (proposed default: remove it and its
  tests, with a `removal-4.0` registry entry for `ChatMemberAdapter` pointing to the `ChatMember` union decode) —
  record in Notes and flag to owner.
- [ ] Emit the Rust routing content-kind table with `Update.event_type`; `routing_keys().content_kind` reads it.
- [ ] Fixture tests: the 10 §1 reproduction (`getUpdates` with a valid message plus `ChatMember` status `superadmin`) decodes both updates, the second as `UnknownChatMember` with `.user` set; an unknown update key gives `event_type == "brand_new_update"`; strict mode raises in both cases.
- [ ] Migration-registry entry (PD-13): breaking change 9 (`Unknown…` union members, `event_type` returns unknown names) and the exhaustive-`match` note; verify the A-11 seed. Changelog fragment.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- The 10 §1 reproduction passes: 2 updates are decoded, no exception, one `WARNING` log line.
- Per the recorded decision: with the default, `import aiogram.utils.chat_member` raises `ModuleNotFoundError` and the
  registry has the `ChatMemberAdapter` entry; if kept, it delegates to the generated decoder.
- `routing_keys().content_kind` equals the 3.x `Message.content_type` value for every content kind in the overlay
  (generated test over `content.toml`).
- Every decoded union in the IR has a generated `Unknown…` class, and no request-only union has one (generated test).
- The B-02 bench on the realistic `Update` (pinned A-04 input) is within 3% of C-18 without the Unknown machinery (the unknown branch costs nothing on known data).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Hard error on unknown tags (3.x, aiogram_rust) | Stalls polling forever | D10 |
| Declaration-order fallback | Silent misdecode | D107 |
| `Unknown` for request-only unions | Never decoded | D107 |
| Buffering a tree to pick a variant | Extra pass and allocations | 13 B23 |

## Validation

```bash
cargo clippy --all-targets -- -D warnings
cargo test -p aiogram-core unions
cargo xtask butcher emit && maturin develop --release
uv run pytest tests
cargo xtask butcher check
```

## Workflow notes

- E-09 consumes the routing content-kind table through `Update.routing_keys()`.
- E-14 builds per-update isolation and `unknown_update` dispatch on top of this. D-09 uses it for method responses (`ClientDecodeError` + `.raw`, PD-29).

## Notes

- Coordinator default (reconciliation, K8): the Rust routing content-kind table behind `routing_keys()` is owned here,
  emitted with `Update.event_type`.
