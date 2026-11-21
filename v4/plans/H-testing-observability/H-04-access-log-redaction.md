# H-04 — Access-log redaction wiring

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-02](H-02-token-redaction-filter.md), [E-16](../E-runtime/E-16-webhook-core-aiohttp-sources.md), [E-17](../E-runtime/E-17-asgi-app.md) |
| Blocks | [G-16](../G-features/G-16-cli-run.md) |
| Gate-conditional | no |
| Decisions | D66, R22, D24 |
| Sources | [15-observability.md §5 "Access logs"](../../research/15-observability.md), [19 intro "New issues" + R22](../../research/19-review-resolutions.md), [12-runtime.md §6](../../research/12-runtime.md), [17-cli.md](../../research/17-cli.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`TokenBasedRequestHandler` (kept by D24) puts the bot token in the webhook path, so the default aiohttp access log
writes it to disk. The aiogram logger filters (H-02) don't see third-party loggers. 19 says
`setup_application()` "can't install an access logger", because aiohttp accepts `access_log_class` only in
`run_app` / `AppRunner`.

That limitation is narrower than stated. aiohttp's default `AccessLogger` emits on
`logging.getLogger("aiohttp.access")` (`aiohttp/log.py`), and a **logger-level** filter there covers every record
the default access logger emits. What `setup_application` can't do is cover a *custom* `access_log_class` that
logs elsewhere.

## Scope

**In:**
- **Attach helper (exported):** a public, idempotent helper (proposed
  `aiogram.webhook.attach_access_log_redaction(*loggers=("aiohttp.access",))`) that adds one `TokenRedactingFilter`
  per named logger. G-16 calls it in `aiogram run webhook` for `aiohttp.access`, and for `uvicorn.access` when it
  serves the ASGI app through uvicorn; this plan does not touch G-16's code.
- **`setup_application(app, dp)` attaches the filter to the `aiohttp.access` logger** idempotently, at most one
  instance even across repeated calls. This is a **proposed default that corrects 19 / 15 §5**; flag it to the
  owner.
- The opt-out (`redact_tokens(False)`) covers these filters too, because the filter reads the global flag.
- Extra-field scrubbing: aiohttp passes `first_request_line` and friends through `extra=`. The H-02 filter scrubs
  string `extra` attributes. This plan adds the end-to-end test through a real access log. It is a **proposed
  default to flag** together with H-02.
- Docs (webhook + ASGI deployment pages):
  - where the filter is attached automatically;
  - `handler.addFilter(TokenRedactingFilter())` for custom handlers;
  - custom `access_log_class` loggers must log via `aiohttp.access` or add the filter themselves;
  - uvicorn: `uvicorn.access`, args carry the path;
  - Granian: check whether its access log goes through a Python logger. If yes, document attaching the filter.
    If not, document disabling the access log or using a format without the path. Record the finding in *Notes*;
  - reverse-proxy logs are outside what a library can redact (R22).

**Out:**
- The filter itself (H-02).
- Webhook handler and ASGI internals (E-16/E-17).
- CLI argument parsing and the attach call inside `aiogram run webhook` (G-16, which depends on this plan).

## Checklist

- [ ] Exported attach helper, idempotent per logger (unit test with `aiohttp.access` and `uvicorn.access`).
- [ ] `setup_application`: attach to `aiohttp.access` once through the helper (idempotence test).
- [ ] End-to-end test: an aiohttp test server with `TokenBasedRequestHandler` registered at a path containing
      `{bot_token}`, built through `setup_application`, run with the default `AccessLogger`. A test handler on
      `aiohttp.access` renders with both `logging.Formatter` and a JSON formatter over `record.__dict__`. Assert the
      fabricated token is absent and `<id>:***` is present.
- [ ] Same test for the ASGI app under uvicorn's access logger, if uvicorn is in the test group. Otherwise test a
      record shaped like uvicorn's (`'%s - "%s %s HTTP/%s" %d'` with args) on a logger with the filter.
- [ ] Granian check recorded in *Notes* and reflected in the docs.
- [ ] Docs updates as listed in Scope.
- [ ] Changelog fragment.

## Acceptance criteria

- The fabricated token is absent from both formatters' output for a `TokenBasedRequestHandler` request served via
  `setup_application`.
- Calling `setup_application` twice, or the helper twice, leaves exactly one `TokenRedactingFilter` on
  `aiohttp.access`.
- With `redact_tokens(False)`, the token is present (the opt-out works for access logs).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Documenting only, with no automatic attach in `setup_application` (19 wording) | The default access logger is reachable through its logger name, so leaving the default path unredacted contradicts "on by default" | D66; proposed default, flag to owner |
| A custom `access_log_class` from aiogram | Only `run_app`/`AppRunner` accept it; `setup_application` users would still leak | 19 "New issues" |
| Attaching filters to third-party loggers at `import aiogram` | Changes other libraries' logging for apps that never run a webhook | D66 scope |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Needs E-16 (aiohttp sources / `setup_application` on the Runner) and E-17 (ASGI app).
- Output: the attach helper and the deployment docs. G-16 performs the attach in `aiogram run webhook`.

## Notes

- Coordinator (cycle fix): this plan exports the attach helper and documents the server setups; the call inside
  `aiogram run webhook` is made by G-16, which depends on this plan.
