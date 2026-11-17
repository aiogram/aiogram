# D-07 — Rust encoder: JSON request body, `Default` resolution, value rules

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [B-09](../B-spike/B-09-sendmessage-encoder-response.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md), [D-01](D-01-default-bot-properties-and-bot-cleanup.md), [C-21](../C-butcher/C-21-generated-tests-emitter.md) |
| Blocks | [D-08](D-08-rust-encoder-multipart.md), [D-10](D-10-request-snapshot-and-render-hook.md), [D-11](D-11-session-on-new-codec.md), [D-13](D-13-raw-bot-call-raw-method.md), [D-14](D-14-webhook-reply-encoding.md), [D-15](D-15-request-response-differential-cases.md), [F-12](../F-fsm/F-12-aiogram-types-in-fsmdata.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | D5, D96–D99 (D99 forwarding), D87, R18, PD-11, PD-20, PD-23 |
| Sources | [05-network.md §2.1](../../research/05-network.md), [01-models.md §3.1, §3.3](../../research/01-models.md), [13-aiogram-rust-review.md §3 B17](../../research/13-aiogram-rust-review.md), [19 §2 R18](../../research/19-review-resolutions.md), [08-build-release.md §7](../../research/08-build-release.md), [plans README §1](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x encodes `SendMessage` (3×3 keyboard + 3 entities) in 93 µs: `model_dump()` + recursive
`BaseSession.prepare_value` + urlencoded `FormData` (`AiohttpSession.build_form_data`). JSON body alone is 21.4 µs
(05 §1; 3.x quick win 3x-09). The 4.0 encoder walks the Rust method struct directly and returns a ready JSON body.
B-09 built it for `SendMessage` only; this plan generalises it to every generated method.

## Scope

**In:**
- `aiogram._core.encode(method, defaults) -> JsonBody | Multipart` entry point (`JsonBody(bytes)`); this plan
  implements the no-files branch for all methods; the multipart branch is D-08 (until then, a method with an
  `InputFile` raises `NotImplementedError` behind a test-only path).
- Encoder runtime in hand-written Rust (e.g. `crates/aiogram-core/src/encode/`), driven by the per-method field
  tables emitted by C-20 — no per-method hand code; follow 08 §7 placement rules (per-class bodies as trait methods,
  hoisted class-independent code, `#[inline(never)]` bodies).
- `Default("name")` resolution against the per-bot defaults snapshot (built once per `DefaultBotProperties` object
  from D-01's accessor, cached on the Rust side by object identity — PD-20 makes it immutable). Applies to nested
  values too (`InputMedia*.parse_mode`, `InputTextMessageContent.parse_mode`, `link_preview_options`). A default
  that resolves to `None` omits the field.
- Value rules:
  - DateTime fields: `datetime` → unix seconds, **naive = local time** (`datetime.timestamp()` semantics),
    half-even rounding; **`timedelta` → `now + delta` as absolute unix time** (PD-11; 3.x
    `BaseSession.prepare_value` does the same). "timedelta as seconds" (13 B17 / 05 §2.1 / 01 §3.1) is a bug.
  - Enums → their value; unknown enum strings and `Unknown…` union members re-encode their wire shape unchanged.
  - Aiogram types nested in params → wire shape (same as `to_dict()`), wire names (`from`).
  - `None` fields omitted.
- D99 extras: unknown kwargs stored on the method (JSON-shaped, D87) are forwarded verbatim. The one-time
  `AiogramUnknownParameterWarning` (class defined by I-12) is raised by C-20's generated constructors, not here. Stubs carry no `**extra` (PD-23).
- `TelegramMethod.to_json()` (model representation, R18): wire JSON of set fields, **unresolved `Default` omitted**,
  raises `TypeError` for `InputFile` values. Ready requests are built only by `encode`.
- Python-visible types `JsonBody` / `Multipart` declared in the `.pyi` (Multipart filled in by D-08).

**Out:**
- Multipart / files → D-08. Lazy text rendering hook and snapshot → D-10.
- Raw `bot.call` generic path → D-13. Session wiring → D-11. Webhook replies → D-14.
- Emitting the field tables → C-20.

## Checklist

- [ ] Encoder runtime over C-20 tables; one coarse call per request (08 §7 rule 1).
- [ ] Defaults snapshot conversion + identity cache; nested `Default` resolution.
- [ ] DateTime rules incl. `timedelta` → `now + delta` (PD-11); test with a frozen clock.
- [ ] Record the Windows naive-datetime difference: 3.x on `win32` treats naive datetimes as UTC
      (`aiogram/types/custom.py`, `_datetime_serializer` win32 branch); 4.0 treats them as local time on every OS.
      Add it as an approved difference in the D-15 manifest (PD-11) and a migration-registry entry (PD-13).
- [ ] Unknown enum / Unknown union re-encode round-trip.
- [ ] D99 extras forwarded.
- [ ] `TelegramMethod.to_json()` semantics (R18).
- [ ] Decide whether `encode` releases the GIL (`py.detach`) for large bodies (proposed default: no; 08 §7 rule 7
      applies only to ≥1 ms work, which a request body never reaches) — record in Notes.
- [ ] clippy restriction lints clean (no `unwrap`/`expect`/`panic`, 08 §5).
- [ ] Bench on A-04 case `request.sendMessage.plain` (the pinned `SendMessage` 3×3 keyboard + 3 entities input) via
      the B-02/A-05 harness.
- [ ] Tests (100% Python coverage of new code; Rust unit tests for value rules).
- [ ] Changelog fragment (`feature`: JSON request bodies).

## Acceptance criteria

- For every generated method in the C-21 per-method encode fixtures, `encode(...)` output parses to the expected
  wire dict.
- `BanChatMember(chat_id=1, user_id=2, until_date=timedelta(hours=1))` encodes `until_date` within ±1 s of
  `now + 3600` (frozen clock), never `3600`.
- `SendMessage(chat_id=1, text="x", parse_mode=Default("parse_mode"))` with `DefaultBotProperties(parse_mode="HTML")`
  encodes `"parse_mode":"HTML"`; with no default the key is absent.
- `InputMediaPhoto(media="id", caption="c")` nested in `SendMediaGroup` gets the default `parse_mode`.
- `SendMessage(...).to_json()` omits an unresolved `Default` field and raises `TypeError` when a field holds an
  `InputFile`.
- Bench: encode of A-04 case `request.sendMessage.plain` is at least 4× faster than the optimised-3.x JSON path recorded by
  A-06 (3x-09 tag), median of 7, warm process, Linux + macOS.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `timedelta` as duration seconds | Turns temporary bans into permanent ones | PD-11 |
| Always multipart (aiogram_rust) | Larger, slower; JSON accepted for all methods | 05 §2.1, 13 §4 |
| Python fallback encoder | No pure-Python fallback | D1 |
| `#[derive(Serialize)]` per method | Build-time cost; table-driven like decode | 13 B1, B3 |
| Rebuild defaults struct per call | Unneeded once `DefaultBotProperties` is frozen | PD-20 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
make dev            # maturin develop
uv run pytest tests
uv run mypy aiogram
cargo xtask butcher check
make lint
make bench          # release build; record numbers in the PR
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases request.sendMessage.plain,request.sendMessage.defaults
```

## Workflow notes

- Inputs: B-09 (SendMessage encoder prototype), C-20 (encoder tables), C-21 (per-method encode fixtures), D-01
  (defaults accessor).
- Outputs: `_core.encode`, `JsonBody` for D-08, D-10, D-11, D-13, D-14; differential cases in D-15.
- Can run in parallel with D-09 after B-13.

## Notes
