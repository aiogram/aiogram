# G-16 — `aiogram run polling` / `aiogram run webhook`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-15](G-15-cli-core.md), [E-13](../E-runtime/E-13-runner-lifecycle-bot-registry.md), [E-15](../E-runtime/E-15-poller.md), [E-16](../E-runtime/E-16-webhook-core-aiohttp-sources.md), [H-04](../H-testing-observability/H-04-access-log-redaction.md), [E-18](../E-runtime/E-18-compat-wrappers.md), [E-23](../E-runtime/E-23-bot-registry.md) |
| Blocks | [G-17](G-17-cli-reload.md) |
| Gate-conditional | no |
| Decisions | D76, D21–D24, D66, R22, R30 |
| Sources | [17-cli.md §1](../../research/17-cli.md), [12-runtime.md](../../research/12-runtime.md), [19 R22, R30](../../research/19-review-resolutions.md), [codex-review.md R30](../../research/codex-review.md), [15-observability.md](../../research/15-observability.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`aiogram run polling app:dp` should start a production-ready bot without a hand-written `main()`. It goes through
the same `Runner` (12) that user code uses, so behaviour is identical, including shutdown hooks and token-safe
access logs.

## Scope

**In:**
- **App resolution** for `<module:attr>`: a `Dispatcher` instance, a factory, or a coroutine function returning one.
  The default attribute names are `dp` and `dispatcher`. The module is imported with the current directory on
  `sys.path`. A clear usage error (exit `2`) if nothing resolves.
- **`run polling`**: builds a `Runner` with a `Poller` (E-13 / E-15) and adds one bot per token.
  - Tokens come from `--token` / `$BOT_TOKEN`, repeated or comma-separated (G-15 helper), or `--token-file`.
  - Options:
    - `--skip-updates` (drop pending updates on start);
    - `--api URL` (local Bot API server, `TelegramAPIServer`);
    - `--log-level`, `--log-format` (H-01);
    - `--allowed-updates` (default: derived from the routing snapshot).
- **`run webhook`**: serves the aiohttp webhook source (E-16).
  - Options: `--host`, `--port`, `--path`, `--secret-token`, and `--set-webhook URL`, which calls `setWebhook` on
    start.
  - **Multi-bot needs an explicit `--bot TOKEN=PATH[:SECRET]` mapping per bot** (R30); repeated tokens are rejected
    for webhook.
  - The CLI calls H-04's exported attach helper for `aiohttp.access` (and `uvicorn.access` when serving the ASGI
    app through uvicorn) (R22).
- Signals and lifecycle: the main-thread Runner owns SIGINT/SIGTERM (R12). `dp.startup` / `shutdown` fire once.
- Workflow data: none from the CLI beyond what the app sets. `bots` / `dispatcher` reach handlers through the Runner.

**Out:**
- `--reload`: G-17.
- ASGI serving from the CLI: not in 17. Users run uvicorn/granian on E-17's app.
- Webhook management outside `run` (`bot webhook set/delete`): G-18.

## Checklist

- [ ] Resolver for `module:attr` (instance / factory / coroutine); tests for each and for failure.
- [ ] `run polling` with all options; multi-bot polling.
- [ ] `run webhook` with all options, `--bot` mapping, and `--set-webhook`.
- [ ] Attach the H-04 access-log filter. Test that a request path containing a token is masked in the access log.
- [ ] **Decide webhook setup failure and rollback** (R30). Proposed default: if `--set-webhook` fails for any bot,
      the server does not start; webhooks already set by this run are deleted, the error is printed redacted, and
      the exit code is `1`. Record in Notes and flag to owner.
- [ ] **Decide whether `run webhook --set-webhook` deletes the webhook on shutdown** (proposed default: no, unless
      `--delete-webhook-on-exit` is given) — record in Notes.
- [ ] **Decide whether `run webhook` authenticates the secret before creating on-demand bots** (R30). Proposed
      default: there are no on-demand bots from the CLI; only mapped bots are served and unknown paths get 404.
      Record in Notes.
- [ ] Prerequisite check: the 3.x webhook fixes are external prerequisites, not plans:
  - the held-back webhook fixes;
  - dropped background tasks on shutdown.

  (The missing `dispatcher` webhook kwarg is already fixed by #1856, and `bots` is polling-only by design, so neither
  is a prerequisite.)

  Confirm E-16 covers each in 4.x. Record the status in Notes rather than assuming they shipped (R30).
- [ ] Docs: deploying page (polling, webhook, multi-bot mapping, reverse proxy note that external proxy logs are not
      redacted).
- [ ] Tests (100% coverage of new code): in-process runs with MockedBot / a fake session and a short-lived server on
      port 0. Cover startup failure, SIGINT shutdown (shutdown hooks ran) and the multi-bot mapping.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- `aiogram run polling tests_app:dp --token-file t.txt` starts, processes one fake update and exits cleanly on
  SIGINT, with `dp.shutdown` called once (subprocess test).
- `aiogram run webhook app:dp --bot T1=/a:S1 --bot T2=/b:S2` routes `/a` to bot 1 and `/b` to bot 2, rejects a wrong
  secret with 401/403, and returns 404 for `/c`.
- No token appears in stdout, stderr or the access log in any test (grep assertion over captured output).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Repeated `--token` for webhook multi-bot | URL/secret mapping is ambiguous | R30 |
| A Rust webhook server | aiohttp + ASGI cover it | D24, 05 §3 |
| Echoing the token in startup logs | Token redaction on by default | D66 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: G-15 (plugin API, token helper), E-13 (Runner), E-23 (bot registry), E-15 (Poller), E-16 (webhook core + aiohttp source), H-04
  (access-log redaction wiring).
- Output: G-17 wraps these commands. I-20 (examples smoke) can use `aiogram run`.

## Notes
