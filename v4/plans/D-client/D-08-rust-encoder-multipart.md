# D-08 — Rust encoder: multipart bodies and file extraction

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md), [D-04](D-04-drop-aiofiles-input-file-replayable.md), [D-07](D-07-rust-encoder-json.md), [B-09](../B-spike/B-09-sendmessage-encoder-response.md) |
| Blocks | [D-10](D-10-request-snapshot-and-render-hook.md), [D-11](D-11-session-on-new-codec.md), [D-13](D-13-raw-bot-call-raw-method.md), [D-14](D-14-webhook-reply-encoding.md), [D-15](D-15-request-response-differential-cases.md), [D-16](D-16-cancellation-resource-tests.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | R18, D97, 05 §2.1 |
| Sources | [05-network.md §2.1](../../research/05-network.md), [02-butcher.md §2 (multipart `encoding`)](../../research/02-butcher.md), [02-butcher.md §5.1 (InputFile stays Python)](../../research/02-butcher.md), [19 §2 R18](../../research/19-review-resolutions.md), [codex-review.md R18](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Methods carrying an `InputFile` (top-level `photo=FSInputFile(...)`, or nested in `media=[InputMediaPhoto(...)]`)
must be sent as `multipart/form-data`. The OpenAPI schema's `encoding` map (34 multipart bodies) says which parts are
JSON-encoded. `InputFile` stays a plain Python class (02 §5.1); the encoder recognises it with `isinstance` and hands
it back to Python, which streams `InputFile.read()`.

3.x: `BaseSession.prepare_value` replaces each `InputFile` with `attach://<secrets.token_urlsafe(10)>` and
`AiohttpSession.build_form_data` adds file parts.

## Scope

**In:**
- `encode(...)` returns `Multipart(fields: tuple[tuple[str, bytes], ...], files: tuple[tuple[str, InputFile], ...])`
  whenever at least one `InputFile` is present anywhere in the method (including inside lists/types).
- Field values: strings as-is, everything else JSON-encoded per the schema `encoding` map (C-20 tables); nested
  `InputFile` replaced by `attach://<name>`.
- Attachment names deterministic (see Decide item).
- `Default` and value rules exactly as D-07 (shared code path).
- Python helper to turn `Multipart` into an aiohttp body (used by D-11 and D-14); filename = `InputFile.filename or
  name`, payload = `InputFile.read(bot)`.

**Out:**
- Streaming / session wiring → D-11. Snapshot and replayability bookkeeping → D-10.
- Webhook multipart replies → D-14. Raw-call generic path (`InputFile` in arbitrary dicts) → D-13.

## Checklist

- [ ] Multipart branch in the encoder; file extraction at any depth.
- [ ] `encoding`-map-driven JSON parts.
- [ ] Decide attachment naming (proposed default: deterministic `file0`, `file1`, … in field-walk order; listed as an
      approved difference vs 3.x random names in the D-15 manifest) — record in Notes and flag to owner.
- [ ] Decide whether a top-level file field is sent as `photo=attach://file0` + part `file0` (3.x behaviour) or as a
      part named `photo` directly (proposed default: keep 3.x `attach://` form for every file; both are accepted by
      Telegram and it keeps one code path) — record in Notes.
- [ ] Python `Multipart` → aiohttp body helper.
- [ ] Tests: `SendPhoto` with `FSInputFile`, `SendMediaGroup` with mixed file/`file_id` media, `InputSticker` lists,
      `InputPaidMedia`, a method without files still returns `JsonBody`.
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragment (`misc`).

## Acceptance criteria

- Every C-21 per-method encode fixture with an `InputFile` yields `Multipart` with the expected field set and file
  names; no `InputFile` appears in any JSON part.
- Encoding the same method twice yields identical `fields` (determinism).
- An upload against a local aiohttp echo server reproduces the file bytes (sha256) for `FSInputFile`,
  `BufferedInputFile` and `URLInputFile`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rust reads files | `InputFile.read()` is an async Python generator; no async Rust | 02 §5.1, README rules |
| Always multipart | JSON when no files | 05 §2.1 |
| Random attach names | Non-deterministic traces break the differential harness | R26 (see Decide item) |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
make dev
uv run pytest tests
uv run mypy aiogram
cargo xtask butcher check
make lint
```

## Workflow notes

- Inputs: D-07 encoder, C-20 `encoding` tables, D-04 `InputFile` IO.
- Outputs: `Multipart` consumed by D-10, D-11, D-13, D-14; cases in D-15; upload paths fuzzed in D-16.

## Notes
