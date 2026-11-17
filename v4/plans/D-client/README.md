# Story D — Client & wire

**Goal.** Move the CPU-bound request/response work to the Rust core while `Bot`, `BaseSession` and `AiohttpSession`
stay Python (D5). The story covers:
- encoding: a JSON body or multipart with `Default` resolution, plus the response decoder with per-update isolation;
- raw `bot.call` (D96–D98);
- webhook replies (R18) and the download/upload lifecycle (D46, D67);
- `ErrorReason` on `e.reason` (D47) and token-safe exceptions (R22);
- the entity-rendering kernel (PD-15).

Read the research pages: [05-network](../../research/05-network.md), [01-models §3.3](../../research/01-models.md),
[10-forward-compatibility](../../research/10-forward-compatibility.md) and
[19-review-resolutions](../../research/19-review-resolutions.md). The planning decisions in [../README.md §1](../README.md)
are normative.

**Exit gate (README D121, milestone D).** Request/response differential cases with difference manifests (R26,
[D-15](D-15-request-response-differential-cases.md)), hook-compatibility tests ([D-12](D-12-custom-session-hook-compatibility.md))
and cancellation/resource tests ([D-16](D-16-cancellation-resource-tests.md)) all pass.

**Not in D.** `RetryMiddleware` (G-13), `RateLimitMiddleware` (G-14), log redaction filters (H-02, H-04) and
`API_CALL` spans (H-07) live in other stories. D provides what they consume (see *Interfaces*).

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [D-01](D-01-default-bot-properties-and-bot-cleanup.md) | Frozen `DefaultBotProperties`, `Bot` cleanup, `Bot.__repr__` | A-01, A-11, C-15 | no | S |
| [D-02](D-02-exceptions-error-reason-restarting-removal.md) | `e.reason`, `RestartingTelegram` removal, `ClientDecodeError.raw` | A-01, A-11, C-12 | no | M |
| [D-03](D-03-token-safe-network-errors.md) | Token-safe network errors (`from None`, `.original`) | A-01, A-11 | no | S |
| [D-04](D-04-drop-aiofiles-input-file-replayable.md) | Drop aiofiles; `InputFile.replayable` | A-01, A-11 | no | S |
| [D-05](D-05-download-lifecycle.md) | Download lifecycle: per-phase timeouts, `bot.stream()` | D-03, D-04 | no | M |
| [D-06](D-06-request-middleware-manager.md) | Request middleware manager: prebuilt chain, anchors | A-01, H-01 | no | S |
| [D-07](D-07-rust-encoder-json.md) | Rust encoder: JSON body, defaults, value rules (PD-11) | B-01, B-09, B-13, C-20, C-21, D-01 | yes | L |
| [D-08](D-08-rust-encoder-multipart.md) | Rust encoder: multipart and file extraction | B-01, B-09, B-13, C-20, D-04, D-07 | yes | M |
| [D-09](D-09-response-decoder.md) | Response decoder, `getUpdates` isolation | B-01, B-09, B-13, B-14, C-18, C-19, C-20, D-02 | yes | L |
| [D-10](D-10-request-snapshot-and-render-hook.md) | Request snapshot + render hook (PD-07) | B-01, B-09, B-13, D-04, D-06, D-07, D-08 | yes | M |
| [D-11](D-11-session-on-new-codec.md) | `BaseSession`/`AiohttpSession` on the codec (PD-08) | D-01, D-02, D-03, D-06, D-07, D-08, D-09, D-10, H-19, I-12 | yes | L |
| [D-12](D-12-custom-session-hook-compatibility.md) | Custom-session hook compatibility | D-11 | yes | M |
| [D-13](D-13-raw-bot-call-raw-method.md) | Raw `bot.call` + `RawMethod` | B-01, B-13, C-20, D-07, D-08, D-09, D-11 | yes | M |
| [D-14](D-14-webhook-reply-encoding.md) | Webhook reply encoding; `deserialize_telegram_object` | D-01, D-07, D-08, D-10 | yes | M |
| [D-15](D-15-request-response-differential-cases.md) | Request/response differential cases (exit gate) | A-07, A-09, D-07, D-08, D-09, D-11, D-12, D-13 | yes | M |
| [D-16](D-16-cancellation-resource-tests.md) | Cancellation/resource tests (exit gate) | D-03, D-04, D-05, D-08, D-11 | yes | M |
| [D-17](D-17-rust-entity-rendering-kernel.md) | Rust entity-rendering kernel (PD-15) | 3x-17, B-01, B-10, B-13 | yes | L |

## Order and parallel lanes

1. **Before the B gate.** These are Python only and can run in parallel: D-01, D-03, D-04, D-06 (after H-01) and
   D-02 (merges after C-12). D-05 follows D-03 and D-04.
2. **After B-13 says go**, with C-19 and C-20 available:
   - **Lane A (encode):** D-07 → D-08 → D-10.
   - **Lane B (decode):** D-09.
   - **Lane C:** D-17, independent of the rest.
3. **Session.** D-11 starts once lanes A and B are done.
4. **After D-11, in parallel:** D-12, D-13 and D-14 (D-14 needs only D-10).
5. **Exit gate:** D-15 and D-16 in parallel.

## Interfaces other stories rely on

| Consumer | What D provides | Plan |
|---|---|---|
| E-14, E-15 | `getUpdates` tuple with decode-error updates (always with `update_id`); `DecodePolicy` | D-09 |
| E-14, E-16 | Capture function for handler-returned methods (PD-07) | D-10 |
| E-16, E-17 | `encode_webhook_reply` / `WebhookReply` (streamed multipart) | D-14 |
| G-06 | Encoder render callback, one render for text and entities | D-10 |
| G-08, G-09 | Entity kernel: UTF-16, unparse, quoting, tree render | D-17 |
| G-13 | Anchors (Retry outermost); `TelegramRetryAfter`; `request_sent` on network errors; `replayable` + consumed flags; snapshot reuse; `RawMethod` is non-idempotent (PD-25) | D-06, D-03, D-04, D-10, D-13 |
| G-14 | Anchors; `chat_id` on methods and in `RawMethod.params` | D-06, D-13 |
| H-02, H-04 | No token in exception text; `Bot.__repr__` shows the id only; token-absence test helper | D-03, D-01 |
| H-07, H-09 | Anchors; per-attempt status and call info; `e.reason`, `status_code` | D-06, D-11, D-02 |
| H-10, H-19 | Stable custom-session contract (typed method objects incl. `RawMethod`); updated `MockedSession` | D-12, D-11 |
| H-16 | Canonical request/response traces and corpus | D-15 |
| I-16, I-19 | Migration-registry entries for D's breaks (each plan adds its own) | all |

## Open decisions recorded in plans

Each of these is a "Decide (proposed default)" checklist item. The implementing session records the outcome in that
plan's Notes and flags it to the owner.

| Decision | Plan |
|---|---|
| Is `bot.default` reassignment supported? | D-01 |
| What does `ClientDecodeError.raw` hold for a non-JSON envelope? | D-02 |
| How is a known-not-sent network error classified (`request_sent`)? | D-03 |
| Default `replayable` for custom `InputFile` subclasses | D-04 |
| `DownloadTimeout` defaults; `stream_content` shim for custom sessions | D-05 |
| How the per-call timeout and context are carried through the cached chain | D-06, D-10 |
| GIL release in `encode` | D-07 |
| Attachment naming; top-level file form | D-08 |
| Python-visible `decode_response` shape | D-09 |
| How HTTP status and response info reach middlewares | D-11 |
| `prepare_value` slow path; `check_response` contract | D-12 |
| What `aiogram.Raw` is | D-13 |
| Which 3.x oracle tag D compares against | D-15 |
| Formatting-tree render input shape | D-17 |
