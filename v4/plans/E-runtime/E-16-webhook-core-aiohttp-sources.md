# E-16 — Webhook core and aiohttp sources

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-14](E-14-feed-paths-forward-compat-dispatch.md), [D-14](../D-client/D-14-webhook-reply-encoding.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [D-09](../D-client/D-09-response-decoder.md), [E-23](E-23-bot-registry.md); external prerequisite: the 3.x webhook fixes (background-task drain on shutdown, and the held-back webhook fixes) merged on `dev-3.x` and forward |
| Blocks | [E-17](E-17-asgi-app.md), [E-18](E-18-compat-wrappers.md), [G-16](../G-features/G-16-cli-run.md), [H-04](../H-testing-observability/H-04-access-log-redaction.md), [E-21](E-21-e-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D21, D23, D24, R12, R18, R22, D10 |
| Sources | [12-runtime.md §6, §7](../../research/12-runtime.md), [05-network.md §2.4](../../research/05-network.md), [19 R12, R18, R22](../../research/19-review-resolutions.md), [codex-review R13](../../research/codex-review.md), [15-observability.md](../../research/15-observability.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The 3.x webhook (`aiogram/webhook/aiohttp_server.py`: `setup_application`, `BaseRequestHandler`,
`SimpleRequestHandler`, `TokenBasedRequestHandler`) has its own lifecycle, decodes via `request.json()` +
`model_validate`, builds a `MultipartWriter` for every reply, and the reply-or-background timeout logic lives in
`Dispatcher.feed_webhook_update`. Background tasks are only kept from GC, so they die on shutdown. D24 keeps the two
bot-lookup classes but makes them Runner sources over one webhook core shared with ASGI (E-17).

## Scope

**In:**
- **Webhook core** (framework-neutral, proposed `aiogram/webhook/core.py`): input = bot + raw body bytes (+ secret
  header); output = status + headers + body, where the body is `bytes | AsyncIterable[bytes]` (D-14's
  `WebhookReply.body`, streamed by E-17 with `more_body`); no reply method (`None`) answers with JSON `{}` per D-14. Decodes through `runner.process` / `runner.feed` (E-14), which
  call D-09's `decode_update(raw, bot)`.
  - a handler-returned method arrives already captured (PD-07: captured at handler return, inside the middleware
    scope, at E-02's handler-result seam where G-06 installs D-10's capture); the core only encodes it as the reply
    (D-14) or sends it as a background silent call; a failing background call (including a `RetryMiddleware` give-up,
    G-13) is reported through E-12's `emit_runtime_error` (E-11's `phase=WEBHOOK_REPLY`);
  - inline mode: run via `runner.process`; answer with the reply method encoded by D-14 (JSON without files,
    multipart with files, R18) within the reply window (≈55 s, 3.x `_timeout`); past the window, answer 200 and
    finish in the background, sending the method by a normal call (silent-call path);
  - background mode (`handle_in_background=True`, the 3.x default on both handlers): answer 200 immediately; the task
    is admitted and tracked by the Runner, so shutdown waits for it; **`max_pending`** cap — beyond it answer 5xx so
    Telegram redelivers (R12);
  - decode failure in lenient mode: 200 (poison update isolated, D10); errors in background replies →
    `runtime_errors(phase=WEBHOOK_REPLY)`.
- **Sources:** `SimpleRequestHandler(runner_or_dp, bot, secret_token=...)` and `TokenBasedRequestHandler(...)` become
  `UpdateSource`s: `handler.register(app, path)` + `runner.attach(handler)`. TokenBased creates bots on demand via
  `runner.add_bot` (E-23's registry), so `bot_added` fires. Keep the 3.x-track webhook fixes (background-task tracking and
  the held-back webhook fixes). The `dispatcher` webhook kwarg is already fixed on 3.x (#1856) and `bots` is
  polling-only by design, so neither is a prerequisite.
- `setup_application(app, dp, **kw)`: builds a Runner and hooks it to aiohttp `on_startup` / `on_cleanup`; startup and
  shutdown emitted once (by the Runner).
- `dp.feed_webhook_update(bot, update, **kw)`: kept, delegates to the core.
- Handler data identical for polling and webhook (`bots`, `dispatcher`, workflow data; 03 §5).
- Docs: webhook page rewritten; access-log token exposure note (`setup_application` can't install a custom
  `access_log_class`; H-04 attaches the redaction filter to the `aiohttp.access` logger).

**Out:**
- Reply encoding (D-14); ASGI app (E-17); access-log redaction filter (H-02/H-04); CLI `run webhook` (G-16).

## Checklist

- [ ] Framework-neutral core with inline / background modes, reply window, `max_pending`.
- [ ] Reply / background silent call use the already-captured call (no capture in the core); background failures →
  `emit_runtime_error` (`phase=WEBHOOK_REPLY`).
- [ ] aiohttp adapter: body as bytes, secret header check, response building from the core output.
- [ ] `SimpleRequestHandler` / `TokenBasedRequestHandler` as sources; TokenBased → `runner.add_bot`.
- [ ] `setup_application` on a Runner; `feed_webhook_update` wrapper.
- [ ] Decide the HTTP status matrix (codex R13) (proposed default: bad/missing secret → 401; unknown bot / token not
  allowed → 404; body over the size limit → 413; `max_pending` exceeded or Runner not serving → 503; undecodable body
  in lenient mode → 200; strict mode decode error → 200 plus `errors(DECODE)`; handler exception in inline mode →
  200 with the D-14 `None` reply (JSON `{}`) after `errors` handling, 500 only if the core itself fails) — record in Notes and flag to owner.
- [ ] Decide the default `max_pending` (proposed default: `4 × tasks_concurrency_limit`, or 1 000 when the limit is
  `None`) — record in Notes and flag to owner.
- [ ] Changelog fragment(s); migration-registry entries (PD-13) for any changed defaults/statuses relative to 3.x.
- [ ] Tests (aiohttp test client): inline reply JSON and multipart, reply-window overflow, background tracked across
  shutdown (no dropped update), `max_pending` 503, secret mismatch, TokenBased `bot_added`, poison body 200.

## Acceptance criteria

- Shutdown with 10 in-flight background updates completes all 10 before `on_cleanup` returns (or cancels them at the
  `tasks_shutdown_timeout` deadline and reports them).
- Reply bodies are `application/json` when the method has no files and `multipart/form-data` otherwise (R18); an
  update with no reply method answers 200 with JSON `{}`; a multipart body is streamed, not buffered.
- Startup/shutdown hooks fire exactly once for an app with two handlers.
- Per-request CPU on the A-05 webhook loopback scenario ≤ the A-06 optimised-3.x baseline.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rust web server | ≈60–70 µs aiohttp cost vs thread hops into asyncio and a fork-unsafe tokio runtime | D23 |
| New bot-lookup strategies | 3.x Simple / TokenBased kept | D24 |
| Always multipart replies | Larger and slower | R18 |
| Unbounded background tasks | No overload behaviour; R12 asks for a cap | R12 |

## Validation

```bash
make dev
uv run pytest tests/test_webhook -q
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Shares the core with E-17 (ASGI). H-04 attaches the access-log redaction filter in the documented setup.
- The 3.x webhook fixes must be merged forward first; do not re-solve them here.
- Gate: this plan's own design is gate-independent, but it stays blocked until D-09, D-10 and D-14
  (gate-conditional) land. Only body decoding, return-time capture and inline-reply encoding need them: the core,
  sources, background mode and `max_pending` can start against the 3.x session and reply path and switch over when
  those merge.

## Notes

- Coordinator default (reconciliation, K17): the core's body is `bytes | AsyncIterable[bytes]` (D-14 / E-17), and a
  `None` reply is JSON `{}` per D-14.
