# 3x-02 — Webhook: poison updates are logged and answered with 200

| Field | Value |
|---|---|
| Status | `done` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-03](../A-contracts/A-03-poison-update-decision.md) (owner-signed decision record); one external prerequisite (held back until its fix is released) |
| Blocks | [3x-10](3x-10-webhook-json-reply.md), [3x-18](3x-18-unknown-union-fallback.md) |
| Gate-conditional | no |
| Decisions | D10 (3.x mitigation), D120, R13, PD-28 |
| Sources | [09 #22](../../research/09-3x-quick-wins.md), [10 §5](../../research/10-forward-compatibility.md), [19 R13](../../research/19-review-resolutions.md), [A-03](../A-contracts/A-03-poison-update-decision.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

When an update fails validation on the webhook path, `Update.model_validate` raises outside any `try`:
- `Dispatcher.feed_webhook_update` and `feed_raw_update` don't catch it.
- In background mode (`BaseRequestHandler._handle_request_background`), validation runs inside an unawaited task,
  so the exception is lost and asyncio renders the full `ValidationError` (ANT-2026-KMKQCARC: about 7 s of rendering
  for crafted input).

Telegram then redelivers the update until it gives up.

**One PR for the related OSS Scanner findings** ("Webhook validation DoS"). The findings and fix shapes:

| Finding | Fix |
|---|---|
| ANT-2026-KMKQCARC | Validate once in `BaseRequestHandler.handle`, catch `ValidationError`, log `error_count()`, return 200 |
| ANT-2026-HL9BRR9S | Read the body as bytes and decode UTF-8 at both webhook sites; don't honour the sender's charset (punycode is quadratic) |
| ANT-2026-PX6H5HDK | Delete `@lru_cache` on `Update.event_type` and `aiogram/utils/mypy_hacks.py` (the class-level cache pins the last 128 updates) |
| ANT-2026-PI9G2NGU | The "slow response" `warnings.warn` in `feed_webhook_update` must use constant text; update JSON in the text pins memory in the warning registry. Send the body to the logger, gated by level |
| ANT-2026-NM3LC5D1 | `fail_fast` on list schemas via a `TelegramObject.__get_pydantic_core_schema__` hook, pydantic floor ≥ 2.8, `FailFast` in `.butcher/types/RichText/subtypes.yml` |
| ANT-2026-IOHAUKLG | Callable `Discriminator` on `date` for `MaybeInaccessibleMessageUnion`, like `rich_text_union.py`; `discriminator: "date"` in `.butcher` `subtypes.yml`. Needs a butcher generator special case |

## Scope

**In:** everything in the table, following the A-03 decision for webhook status codes and reporting:
- **200 for validation failures.** Telegram stops redelivering. Telegram treats any non-2xx as a failure and
  redelivers.
- 401/403/404 stay for auth and routing failures.

Both `BaseRequestHandler` paths (background and inline) and the direct `Dispatcher.feed_webhook_update(dict)` entry
behave the same way.

**Out:**
- Polling: [3x-01](3x-01-polling-poison-isolation.md).
- The JSON webhook reply: [3x-10](3x-10-webhook-json-reply.md).
- The external prerequisite (held back until its fix is released).
- 4.0 webhook core: E-16.

## Checklist

- [ ] Confirm A-03 is signed off and the external prerequisite has been released. Otherwise set `Status: blocked`.
- [ ] KMKQCARC: validate in `BaseRequestHandler.handle` before choosing background or inline. On `ValidationError`:
  - log once at the A-03 level with `error_count()` and the `update_id` when readable;
  - report as A-03 decides;
  - return `web.json_response({})`.
- [ ] `Dispatcher.feed_webhook_update` with a dict: catch `ValidationError` the same way and return `None`.
- [ ] HL9BRR9S: replace `request.json(loads=…)` with `await request.read()` plus UTF-8 decode at both sites.
      Respect a custom `bot.session.json_loads`.
- [ ] PX6H5HDK: remove the `lru_cache` from `Update.event_type` and delete `aiogram/utils/mypy_hacks.py`, with no
      behaviour change. If the cache is emitted by butcher, change `.butcher` instead.
- [ ] PI9G2NGU: constant warning text; the body goes to `loggers.webhook` at `DEBUG`.
- [ ] NM3LC5D1:
  - add the `fail_fast` hook;
  - raise the pydantic floor in `pyproject.toml` if needed and record it in the changelog;
  - add `FailFast` in `.butcher/types/RichText/subtypes.yml`;
  - regenerate with `butcher apply all`.
- [ ] IOHAUKLG:
  - add the callable discriminator through `.butcher` (not by hand-editing the generated `types/`);
  - if the butcher tool needs a special case, record which package or version and make that change first;
  - drop the scanner's SIGALRM timing test.
- [ ] Tests:
  - an invalid update yields 200 on both handler modes, with no background task exception;
  - a non-UTF-8 charset header is ignored;
  - memory stays bounded across 1 000 distinct updates (no `lru_cache`);
  - the warning registry doesn't grow;
  - deep nested `MaybeInaccessibleMessage` validates in linear time (a size-doubling test, no wall-clock thresholds).
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.bugfix.rst`. List each finding and end with "Reported by the Anthropic OSS
      Scanner (ANT-2026-KMKQCARC, ANT-2026-HL9BRR9S, ANT-2026-PX6H5HDK, ANT-2026-PI9G2NGU, ANT-2026-NM3LC5D1,
      ANT-2026-IOHAUKLG).".
- [ ] One `Reported-by: Anthropic OSS Scanner (ANT-2026-…)` commit trailer per finding.
- [ ] Migration registry: no entry (3.x fix).

## Acceptance criteria

- POSTing an invalid update to `SimpleRequestHandler` in both `handle_in_background` modes returns HTTP 200. No
  "Task exception was never retrieved" is logged, and the dispatcher doesn't run.
- A valid update after an invalid one is handled normally.
- `Update.event_type` holds no references to updates (a `weakref` test).
- Regenerating with butcher keeps the IOHAUKLG and NM3LC5D1 changes: `git diff` is empty after `butcher apply all`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Answer 4xx/5xx for an invalid update | Telegram redelivers forever | D10, 10 §5 |
| Hand-edit `rich_text_union.py` / `maybe_inaccessible_message_union.py` | Regeneration reverts it | AGENTS.md codegen rule |

## Validation

```bash
uv run --extra cli butcher parse && uv run --extra cli butcher refresh && uv run --extra cli butcher apply all
git diff --exit-code -- aiogram/types   # after the .butcher change is committed
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

- Informs E-16 (webhook core) and E-14 (forward-compat dispatch): the 3.x precedent for "invalid update → 200".
- Touches `.butcher`, so C-11 (`import-legacy`) must re-import after this lands, or its diff mode will report it.
- Parallel with every plan that doesn't touch `aiogram/webhook/aiohttp_server.py`. 3x-10 touches the same file, so
  land 3x-02 first.

## Notes


- Owner, 2026-11-18: publish through a **GHSA private fork** (advisory + 3.x minor together; ids only in the advisory
  credit, not in public commits, trailers or changelog fragments). A-03 is signed off, so this plan is ready.
- Owner, later on 2026-11-18: the fix **does** credit the scanner as the checklist says (changelog "Reported by the
  Anthropic OSS Scanner (ANT-…).", a `Reported-by` trailer per finding, credits in the PR body); the bugs are not
  critical enough to hide the credit. Repro code and write-up text still stay out.
- Shipped in aiogram 3.33.0; advisory: https://github.com/aiogram/aiogram/security/advisories/GHSA-hv98-r5fx-wc83.
