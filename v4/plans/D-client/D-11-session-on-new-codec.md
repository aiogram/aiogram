# D-11 — `BaseSession` / `AiohttpSession` on the Rust codec

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [D-01](D-01-default-bot-properties-and-bot-cleanup.md), [D-02](D-02-exceptions-error-reason-restarting-removal.md), [D-03](D-03-token-safe-network-errors.md), [D-06](D-06-request-middleware-manager.md), [D-07](D-07-rust-encoder-json.md), [D-08](D-08-rust-encoder-multipart.md), [D-09](D-09-response-decoder.md), [D-10](D-10-request-snapshot-and-render-hook.md), [H-19](../H-testing-observability/H-19-mockedbot-port.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md) |
| Blocks | [D-12](D-12-custom-session-hook-compatibility.md), [D-13](D-13-raw-bot-call-raw-method.md), [D-15](D-15-request-response-differential-cases.md), [D-16](D-16-cancellation-resource-tests.md), [E-15](../E-runtime/E-15-poller.md), [G-13](../G-features/G-13-retry-middleware.md), [G-14](../G-features/G-14-rate-limit-middleware.md), [H-07](../H-testing-observability/H-07-api-call-spans.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | D5, D45, PD-08, R18, 05 §2.3 |
| Sources | [05-network.md §2.3, §2.5](../../research/05-network.md), [19 §2 R18](../../research/19-review-resolutions.md), [codex-review.md R18](../../research/codex-review.md), [15-observability.md §3](../../research/15-observability.md), [plans README §1 PD-08](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

aiohttp and `BaseSession` stay Python (D5); only encode/decode move to Rust. This plan switches the real request
path to D-07/D-08/D-09: `AiohttpSession.make_request` posts the encoder's body and decodes the bytes with the Rust
decoder. PD-08 simplifies the hooks: session `json_loads`/`json_dumps` **no longer affect the Bot API wire**
(requests, responses and update decoding always use the Rust codec) and are deprecated. That removes the
"fast path only when hooks are default" condition of 05 §2.3.

3.x paths: `aiogram/client/session/base.py` (`BaseSession.__init__`, `check_response`, `prepare_value`, `__call__`),
`aiogram/client/session/aiohttp.py` (`AiohttpSession.build_form_data`, `make_request`), `tests/mocked_bot.py`.

## Scope

**In:**
- `BaseSession`:
  - `json_loads` / `json_dumps` constructor params: accepted, stored, ignored for API traffic; one
    `AiogramDeprecationWarning` when passed (PD-08), emitted through I-12's `warn_deprecated` with its registry id.
  - `__call__` builds the per-call context (D-10) and runs the cached chain (D-06).
  - Public `encode_request(bot, method) -> JsonBody | Multipart` (reads/creates the D-10 snapshot) for custom
    sessions; public `decode_response(bot, method, status_code, content: bytes)` that wraps `_core.decode.decode_response` +
    D-02 `raise_for_error`.
  - `check_response` / `prepare_value` remain defined on the base class for D-12's compatibility path; the default
    request path does not call them.
- `AiohttpSession.make_request`: `encode_request` → `JsonBody` posted as `data=bytes` with
  `Content-Type: application/json`; `Multipart` via the D-08 helper (aiohttp `FormData`/`MultipartWriter` streaming
  `InputFile.read(bot)`); body read with `await resp.read()`; `decode_response`. Errors wrapped per D-03.
  `build_form_data` removed.
- Response/call info for observability: see Decide item.
- `TelegramAPIServer` (local Bot API), proxies (`aiohttp_socks`), `bot.me()` caching: unchanged (05 §2.5).
- Update `tests/mocked_bot.py` (`MockedSession`) to the new hooks; H-19 ports it further.

**Out:**
- Overridden `prepare_value` / `check_response`, old-style custom sessions → D-12.
- Raw calls → D-13. Webhook replies → D-14. FSM storage codecs keep their own hooks (PD-08, PD-22; F story).

## Checklist

- [ ] Deprecate `json_loads`/`json_dumps` (PD-08): warning, documented as ignored for the Bot API wire.
- [ ] `encode_request` / `decode_response` public helpers.
- [ ] `AiohttpSession.make_request` on the codec; remove `build_form_data`; `resp.read()`.
- [ ] Decide how HTTP status and response info reach request middlewares on success (H-07 records
      `status` per attempt) (proposed default: the D-10 per-call context exposes `last_status_code` and
      `attempt` after `make_request` returns; exceptions carry `status_code` from D-02) — record in Notes and flag
      to owner.
- [ ] Update `MockedSession` and existing session tests (`tests/test_api/test_client/test_session/`).
- [ ] Bench: loopback end-to-end `sendMessage` CPU/request vs A-06 baseline (05 §1: 330 µs aiogram vs 146 µs raw
      aiohttp).
- [ ] Tests (100% coverage of new code).
- [ ] Migration-registry entry (PD-13, `deprecation-4.x`): session `json_loads`/`json_dumps` deprecated and ignored
      for API traffic; `build_form_data` removed (`removal-4.0`).
- [ ] Changelog fragments (`feature`, `removal`).

## Acceptance criteria

- With a default `AiohttpSession`, a `sendMessage` without files is sent with `Content-Type: application/json`;
  with an `FSInputFile` it is `multipart/form-data` (local aiohttp test server inspects requests).
- `AiohttpSession(json_dumps=orjson.dumps)` emits one deprecation warning and the request body is byte-identical to
  the default session's.
- No pydantic import on the request path (`sys.modules` check in a subprocess test).
- Loopback bench: aiogram CPU/request at most 1.5× raw aiohttp on the same loopback setup, Linux, median of 7.
- `tests/mocked_bot.py` users in the suite pass unchanged.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Honour user JSON hooks on the wire (fast path only for defaults) | Users with orjson hooks would fall off the fast path; Rust can't call them for nested values | PD-08 |
| Rust HTTP client | tokio bridge cost, fork safety, lost proxy/SSL/trace configs | 05 §3 |
| Shared session per process by default | Sessions stay per bot | D45 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
make dev
uv run pytest tests
uv run mypy aiogram
make lint
make bench
```

## Workflow notes

- Inputs: everything in *Depends on* (I-12: `warn_deprecated` for the PD-08 `json_loads`/`json_dumps` warning).
- Outputs: the production request path for E-15 (Poller), G-13/G-14 (middlewares), H-07 (spans), H-19 (MockedBot),
  D-12/D-13/D-16.

## Notes
