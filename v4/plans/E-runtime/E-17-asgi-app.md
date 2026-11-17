# E-17 — ASGI webhook app

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-16](E-16-webhook-core-aiohttp-sources.md), [D-14](../D-client/D-14-webhook-reply-encoding.md), [E-14](E-14-feed-paths-forward-compat-dispatch.md) |
| Blocks | [E-21](E-21-e-exit-gate.md), [H-04](../H-testing-observability/H-04-access-log-redaction.md) |
| Gate-conditional | no |
| Decisions | D23, D24, R22 |
| Sources | [05-network.md §2.4](../../research/05-network.md), [12-runtime.md §2, §6](../../research/12-runtime.md), [15-observability.md](../../research/15-observability.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D23: no Rust web server; users who want one run Granian or uvicorn over an ASGI app built on the same webhook core as
the aiohttp adapter (raw bytes in → status + bytes out). No extra dependency: the ASGI protocol is plain callables.

## Scope

**In:**
- `aiogram.webhook.asgi` module: an ASGI 3 application wrapping the E-16 core. HTTP `POST` on configured paths; reads
  the body as bytes (with the same size limit), passes the secret header, writes status/headers/body from the core.
- Reply streaming (agreed with D-14): `WebhookReply.body: bytes | AsyncIterable[bytes]`. `bytes` goes out as one
  `http.response.body` message; an async iterable (multipart reply with files) is sent chunk by chunk with
  `more_body=True`, closed by a final message with `more_body=False`. The app never buffers the whole body.
- `lifespan` events start and stop the Runner (or attach to an existing one passed in).
- Bot lookup modes matching D24.
- Docs: running with uvicorn and Granian; access-log token note for uvicorn/Granian (H-04 provides the filter).

**Out:**
- Any framework integration (Starlette/FastAPI) beyond the plain ASGI callable; Rust servers.

## Checklist

- [ ] ASGI app over the core; lifespan support.
- [ ] Send `WebhookReply.body` as `bytes` (one message) or `AsyncIterable[bytes]` (chunks with `more_body=True`, final
  `more_body=False`).
- [ ] Decide the ASGI bot-lookup API (D24 names only the aiohttp classes) (proposed default:
  `WebhookASGIApp(runner, routes={"/bot": SimpleLookup(bot, secret_token=...), "/tg/{bot_token}": TokenLookup(...)})`,
  the lookup objects shared with the aiohttp handlers' logic) — record in Notes and flag to owner.
- [ ] Changelog fragment (`feature`).
- [ ] Tests driving the app with a hand-written ASGI scope/receive/send (no new test dependency): inline reply,
  background, secret mismatch, 503 at `max_pending`, lifespan start/stop.

## Acceptance criteria

- The same E-16 behaviour matrix passes through the ASGI app (shared parametrised test).
- No new runtime dependency in `pyproject.toml`.
- A multipart reply with a file reaches `send` as more than one `http.response.body` message, every one but the last
  with `more_body=True`, and the reassembled body equals D-14's aiohttp output.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Ship a Rust HTTP server | Thread hops and tokio fork issues for no gain | D23 |
| Depend on Starlette | Not needed for a single endpoint | D67–D70 |

## Validation

```bash
make dev
uv run pytest tests/test_webhook -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Gate: blocked until D-14 (gate-conditional) lands, but only reply streaming needs it; the ASGI app, lifespan and
  lookup API can start against the E-16 core with `bytes` replies.
- G-16 (`aiogram run webhook`) may offer an ASGI mode later; not required here.

## Notes
