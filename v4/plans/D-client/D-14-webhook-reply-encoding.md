# D-14 — Webhook reply encoding (JSON / multipart) and `deserialize_telegram_object` on the encoder

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [D-01](D-01-default-bot-properties-and-bot-cleanup.md), [D-07](D-07-rust-encoder-json.md), [D-08](D-08-rust-encoder-multipart.md), [D-10](D-10-request-snapshot-and-render-hook.md) |
| Blocks | [E-16](../E-runtime/E-16-webhook-core-aiohttp-sources.md), [E-17](../E-runtime/E-17-asgi-app.md), [G-06](../G-features/G-06-lazy-text-capture.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | R18, D117 (PD-07), D23 |
| Sources | [05-network.md §2.4](../../research/05-network.md), [12-runtime.md §6](../../research/12-runtime.md), [06-utils.md §2](../../research/06-utils.md), [19 §2 R18](../../research/19-review-resolutions.md), [codex-review.md R18](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

A webhook handler may answer an update inline by returning a method in the HTTP response. 3.x always builds a
`MultipartWriter` (`aiogram/webhook/aiohttp_server.py`, `BaseRequestHandler._build_response_writer`) through
`model_dump()` + `prepare_value`. R18: replies are **JSON when the method has no files, multipart otherwise**
(Telegram accepts multipart replies; they give no result confirmation). `deserialize_telegram_object`
(`aiogram/utils/serialization.py`) keeps its semantics — encoder output plus the method name, defaults resolved,
files extracted — and drops the throwaway `Bot` that costs 4.5 ms (06 §2; 3.x fix 3x-13).

## Scope

**In:**
- `encode_webhook_reply(bot, method_or_captured_call | None) -> WebhookReply` (location e.g.
  `aiogram/webhook/reply.py`): `None` → JSON `{}` (an empty form doesn't work, as 3.x notes); no files → JSON body
  with `"method": <api name>` plus params; files → multipart with a `method` part and streamed file parts.
- Uses the captured render context from D-10 (handler return, PD-07) so lazy text renders with the update's locale.
- `WebhookReply` = status, content type, body; `WebhookReply.body: bytes | AsyncIterable[bytes]` (agreed with E-17):
  JSON and empty replies are `bytes`, multipart replies with files are an async iterable of chunks; aiohttp streams
  the iterable, the ASGI app (E-17) sends each chunk as `http.response.body` with `more_body=True` and a final empty
  chunk with `more_body=False`; no full in-memory buffering.
- `deserialize_telegram_object(obj, default=None, include_api_method_name=True)` and
  `deserialize_telegram_object_to_python(...)`: same signatures and result shape (`DeserializedTelegramObject(data,
  files)`), built on the encoder's wire builtins with defaults resolved from `default` (no `Bot` instance).
- Replace `_build_response_writer` in the aiohttp handler with the new function (E-16 rebuilds the handlers on the
  Runner; this plan provides the encoder side and a minimal swap so 3.x-shaped handlers keep working until then).

**Out:**
- Webhook core, reply-or-background timing, `max_pending`, aiohttp/ASGI sources → E-16, E-17.
- Body decoding (`decode_update`) → D-09 (called via E-14).

## Checklist

- [ ] `encode_webhook_reply` for none / JSON / multipart.
- [ ] Streaming shape (05 §2.4, 12 §2), agreed with E-17: `WebhookReply.body: bytes | AsyncIterable[bytes]`; the
      aiohttp adapter streams the iterable and E-17 sends it with `more_body` — no full in-memory buffering.
- [ ] Captured render context honoured (PD-07).
- [ ] `deserialize_telegram_object(_to_python)` on the encoder, no fake `Bot`; keep `include_api_method_name`.
- [ ] Swap `_build_response_writer` usage.
- [ ] Tests (100% coverage of new code): empty reply, `SendMessage` JSON reply incl. `method` key, `SendPhoto` with
      `FSInputFile` multipart reply, defaults resolution, `tests/test_utils/test_serialization.py` parity.
- [ ] Changelog fragment (`feature`/`misc`: JSON webhook replies).

## Acceptance criteria

- A handler returning `SendMessage(chat_id=1, text="x")` produces `Content-Type: application/json` with body
  `{"method":"sendMessage","chat_id":1,"text":"x"}` (key order free).
- A handler returning `SendPhoto(chat_id=1, photo=FSInputFile(p))` produces `multipart/form-data` whose file part
  matches the file's sha256; file data is streamed (peak RSS for a 20 MB file stays under 5 MB above baseline).
- `deserialize_telegram_object(SendMessage(..., parse_mode=Default("parse_mode")), default=DefaultBotProperties(parse_mode="HTML"))`
  returns data with `parse_mode == "HTML"` and `method == "sendMessage"`, without constructing a `Bot`.
- Existing `test_serialization.py` cases pass unchanged (except approved differences recorded in D-15).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| JSON for every reply | A returned method may contain `InputFile` | R18 |
| Send file replies through the normal client path | Research kept multipart inline replies; client path changes completion/error behaviour | R18 (19 §2) |
| Rust web server | Not shipped | D23 |
| Keep fake `Bot` in `deserialize_telegram_object` | 4.5 ms SSL context per call | 06 §2 |

## Validation

```bash
make dev
uv run pytest tests/test_webhook tests/test_utils/test_serialization.py
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: D-07/D-08 encoder, D-10 capture, D-01 defaults.
- Outputs: `encode_webhook_reply`/`WebhookReply` for E-16 (aiohttp) and E-17 (ASGI).

## Notes
