# 15 — Logging and observability

## 1. Today

- **Loggers:** five in `aiogram/loggers.py` (`aiogram.dispatcher`, `.event`, `.middlewares`, `.webhook`, `.scene`), with about
  28 framework log calls, 11 of them scene debug logs.
- **No context on records:** they are plain `%`-formatted strings with no `extra`, so `update_id`, bot, update type
  and handler can't be correlated.
- **Requests:** `RequestLogging` (request middleware) logs the method name and `bot.id` at INFO under
  `aiogram.middlewares`.
- **Token exposure:** the bot token appears in every API URL (`/bot<token>/method`). `TokenBasedRequestHandler` (kept, D24)
  puts it in the webhook path, so the default aiohttp access log writes it to disk. Network exception texts may also
  contain URLs.
- **No metrics and no tracing.** OpenTelemetry PR #1787 adds async context-manager spans through an `AbstractTracer`.

## 2. Decisions (D63–D66)

| # | Decision |
|---|---|
| **D63** | **The trace hook uses sync span context managers** (revises D54; see 03 §5 "Instrumentation"). `tracer.span(kind, **attrs)` covers `UPDATE`, `ROUTER`, `OUTER_MIDDLEWARE`, `FILTER`, `INNER_MIDDLEWARE`, `HANDLER`, `API_CALL` and `TEARDOWN`. Cost is zero without a tracer; callback consumers use an adapter. Calling rules per R23 (§3) |
| **D64** | **An opt-in OpenTelemetry integration with traces and metrics**: `aiogram[otel]` → `aiogram.contrib.otel.setup(dp, *, tracer_provider=None, meter_provider=None)` |
| **D65** | **Structured logging and a consistent logger hierarchy.** Message texts are unchanged |
| **D66** | **Token redaction is on by default**, with an opt-out |

## 3. OpenTelemetry integration (D64)

- **Tracer calling rules (R23):** tracers are called manually (`__enter__` / `__exit__`) and exited in reverse
  order, with failures logged. Their return value is ignored and the original exception re-raised, so a tracer can
  never suppress or replace an app error. Spans follow a small `Span.set_attribute` protocol.
- **Traces:**
  - one span per `SpanKind` from the D63 hook, named `aiogram.update`, `aiogram.handler <qualname>`, and so on;
  - `API_CALL` spans come from a request middleware placed with the D39 anchors, recording method, HTTP status,
    `ErrorReason` (D47) and the retry attempt (D43). There is one span **per attempt**, inside `RetryMiddleware`,
    which exposes the attempt number (PD-17).
- **Metrics:**

  | Instrument | Type | Attributes |
  |---|---|---|
  | `aiogram.updates` | counter | `update_type`, `outcome` (`handled` / `unhandled` / `error`) |
  | `aiogram.handler.duration` | histogram | `handler`, `router` |
  | `aiogram.api.duration` | histogram | `method`, `status` |
  | `aiogram.api.errors` | counter | `method`, `reason` |
  | `aiogram.runner.inflight` | up-down counter | `bot_id` (registered bots only) |

  Handler names are qualnames; `<lambda>` handlers get a stable registration-site name. Labels are **bounded** (R23):
  chat and user ids are **never** attributes, bot ids created on demand (`TokenBasedRequestHandler`) are not labels,
  and unknown method / update-type names are capped, to avoid high-cardinality labels and PII.
- `opentelemetry-api` is imported lazily and is only needed with the extra. Its free-threading readiness is added to
  the 07 watch list.
- Excluding built-in middlewares from spans is configurable (`exclude=`), as in the PR's draft.

## 4. Logging (D65)

- **Hierarchy:**
  - `aiogram.dispatcher`, `aiogram.runner`, `aiogram.polling`, `aiogram.webhook`, `aiogram.client` (session, requests,
    retries, rate limits), `aiogram.fsm`, `aiogram.scene`, `aiogram.i18n`, `aiogram.event`;
  - `aiogram.middlewares` stays as an alias that receives the same request records, for one deprecation window.
- **Context on every framework record**: `extra={"aiogram_bot_id", "aiogram_update_id", "aiogram_update_type",
  "aiogram_router", "aiogram_handler", "aiogram_phase"}`, set where known. The keys are prefixed, so they never clash with
  user `extra`.
- Inside an update, the values come from a ContextVar set by the Runner (12), so user logs can attach them too:
  `aiogram.loggers.context_filter()` is a `logging.Filter` that copies them onto any record.
- Levels unchanged. Unhandled errors keep `exception` level; `runtime_errors` (D50) fall back to `aiogram.runner`.

## 5. Token redaction (D66)

- A `TokenRedactingFilter` is attached to **every** `aiogram.*` logger at import (Python doesn't apply ancestor
  logger filters to records from child loggers, R22), with a test that walks the logger dict. It masks
  `\d{5,}:[A-Za-z0-9_-]{30,}` as `<id>:***` in message and args, and rewrites a record only when a token matches, to
  keep Sentry grouping. Opt out with `aiogram.loggers.redact_tokens(False)`.
- **Exception text never contains a token** (PD-14): aiogram never builds token-bearing exception text. URLs are
  rendered with `/bot<id>:***/`, and aiohttp errors are wrapped in `TelegramNetworkError` `from None`, with the
  original kept on `.original` (not `__cause__`, which a formatted traceback would print). 3.x fixed its own leak
  in 3.33.0: ANT-2026-4GL80S7S, a raw `ClientResponseError` containing `/file/bot<token>/` from downloads
  ([GHSA-52j5-qrwv-2vf2](https://github.com/aiogram/aiogram/security/advisories/GHSA-52j5-qrwv-2vf2)). The 4.x
  wrapping is owned by D-03 in the client; milestone H owns only the log filters on this page (H-02).
- **Access logs**: a handler-level filter is exported for user handlers and attached to `aiohttp.access` /
  `uvicorn.access` by the CLI and the documented server setup, so `TokenBasedRequestHandler` paths are masked.
  `setup_application(...)` can't install an access logger (aiohttp accepts `access_log_class` only in `run_app` /
  `AppRunner`); this limitation is documented. The ASGI app documents the same for uvicorn and Granian.
- Out of scope: error trackers that capture locals.
- `Bot.__repr__` shows only the bot id.
