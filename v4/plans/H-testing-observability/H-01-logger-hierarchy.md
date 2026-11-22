# H-01 — Logger hierarchy + structured log context

| Field | Value |
|---|---|
| Status | `done` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [H-02](H-02-token-redaction-filter.md), [H-06](H-06-tracing-in-executor.md), [E-02](../E-runtime/E-02-dispatch-table-executor.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md), [D-06](../D-client/D-06-request-middleware-manager.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md), [F-03](../F-fsm/F-03-release-isolation-warn-after.md), [E-13](../E-runtime/E-13-runner-lifecycle-bot-registry.md) |
| Gate-conditional | no |
| Decisions | D65, R23, PD-13, PD-31 |
| Sources | [15-observability.md §4](../../research/15-observability.md), [19 R23](../../research/19-review-resolutions.md), [03-routing.md §5 "Dependencies" (feed_update boundary)](../../research/03-routing.md), [codex-review.md R23](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x has five loggers in `aiogram/loggers.py` (`aiogram.dispatcher`, `.event`, `.middlewares`, `.webhook`, `.scene`)
plus three ad-hoc `logging.getLogger(__name__)` loggers (`aiogram/client/bot.py`,
`aiogram/client/session/middlewares/request_logging.py`, `aiogram/utils/chat_action.py`). Records are plain
`%`-formatted strings with no `extra`, so a log line can't be correlated with `update_id`, bot, update type or
handler (15 §1). D65 asks for a consistent hierarchy and structured context on every framework record.

This task is pulled forward (PD-31): every later 4.0 task logs through these loggers, and H-02 (redaction) hangs
its filter on the same logger factory. It therefore has minimal dependencies and works on the `Dispatcher`
carried over to `dev-4.x` by A-01; E-02/E-14 keep the seam when they rewrite dispatch.

## Scope

**In:**
- `aiogram/loggers.py` is the **only** place framework loggers are created, through one factory
  (`get_logger(name)`, name must start with `aiogram.`). The factory installs the framework record filters on the
  logger (the context filter here; H-02 adds redaction to the same factory).
- Hierarchy (D65): `aiogram.dispatcher`, `aiogram.runner`, `aiogram.polling`, `aiogram.webhook`, `aiogram.client`
  (session, requests, retries, rate limits), `aiogram.fsm`, `aiogram.scene`, `aiogram.i18n`, `aiogram.event`, and
  `aiogram.middlewares` (kept, see below). The three `__name__` loggers move to factory loggers
  (`bot.py` and `chat_action.py` → `aiogram.client`). Message texts and levels are unchanged.
- **Log context** (15 §4, R23): one `ContextVar` holding a small mutable per-update object with
  `bot_id, update_id, update_type, router, handler, phase`. It is **set in `Dispatcher.feed_update`** (the single
  boundary for polling, webhook, Runner sources and direct calls; 03 §5) and reset in `finally`. A nested
  `feed_update` sets its own object and restores the outer one. `router`, `handler` and `phase` are attribute
  writes on that object (no `ContextVar.set` per stage); the executor (E-02) fills them. Until E-02 lands they
  stay `None`.
- A filter on framework loggers copies six keys onto each record: `aiogram_bot_id`, `aiogram_update_id`,
  `aiogram_update_type`, `aiogram_router`, `aiogram_handler`, `aiogram_phase`. They are **always present**, `None`
  when unknown, so `%(aiogram_update_id)s` formats never raise. An attribute already on the record (explicit
  `extra=`) is not overwritten.
- Public `aiogram.loggers.context_filter()` returns a `logging.Filter` that copies the same keys onto any record,
  for user loggers and handlers.
- **`aiogram.middlewares`: no alias.** `RequestLogging` (`client/session/middlewares/request_logging.py`) and
  `CallbackAnswerMiddleware` (`utils/callback_answer.py`) keep logging to `aiogram.middlewares` for one D71 window.
  The request records then move to `aiogram.client`. This is recorded in the registry and the logging docs.
- Unhandled update errors keep `exception` level on `aiogram.event`. `aiogram.runner` is the fallback logger that
  E-12 uses for unhandled `runtime_errors`.

**Out:**
- Token redaction (H-02).
- The trace hook (H-05/H-06).
- OTel (H-08/H-09).
- What Runner/Poller log: E-13/E-15 emit through these loggers.
- The migration-checker rule for `getLogger("aiogram.middlewares")` (I-19 consumes the registry entry).

## Checklist

- [ ] Rewrite `aiogram/loggers.py`: factory, hierarchy, `context_filter()`, the per-update context object +
      `ContextVar`.
- [ ] Replace the three `logging.getLogger(__name__)` call sites with factory loggers.
- [ ] Set/reset the context in `Dispatcher.feed_update` (`aiogram/dispatcher/dispatcher.py`). `bot_id` comes from
      `bot.id`. `update_type` comes from the update's event type, computed by whatever the dispatcher already uses
      (no extra decode).
- [ ] Expose a tiny internal setter for router/handler/phase for E-02 to call (`_log_context()` returning the
      current object or `None`).
- [ ] Guard test: AST scan of `aiogram/**` finds no `logging.getLogger(` call outside `aiogram/loggers.py`.
- [ ] Tests (100% coverage of new code): context present inside `feed_update`, absent (all `None`) outside;
      100 concurrent `feed_update` tasks don't bleed `update_id`; a user logger with `context_filter()` inside a
      **sync** handler (run via `to_thread`) sees the context; nested `feed_update` restores the outer context;
      explicit `extra=` keys are not overwritten.
- [ ] Docs: logging page section "Logger names and record context" (hierarchy table, the six keys, a
      `context_filter()` recipe, the `aiogram.middlewares` window).
- [ ] Migration-registry entry (PD-13, `deprecation-4.x`): request records on `aiogram.middlewares` move to
      `aiogram.client` after the window. Changelog fragment for the new hierarchy and record context.

## Acceptance criteria

- A record from `aiogram.dispatcher` emitted inside `await dp.feed_update(bot, update)` has
  `aiogram_bot_id == bot.id`, `aiogram_update_id == update.update_id` and the correct `aiogram_update_type`.
- Outside an update, all six attributes exist and are `None`.
- `asyncio.gather` of 100 `feed_update` calls with distinct update ids: every captured record carries its own id.
- The guard test fails if a `logging.getLogger("aiogram.x")` call is added anywhere in `aiogram/` except
  `loggers.py`.
- Existing tests that assert log texts pass unchanged.
- Overhead: a `timeit` microbenchmark of one context set/reset pair is ≤ 0.3 µs on the A-01 CI runner, recorded in
  the PR description.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `aiogram.middlewares` as an alias receiving the same records (15 §4) | Both loggers propagate to root, so every root handler prints the record twice | R23, planning resolution (no alias) |
| Context set by the Runner only (15 §4 wording) | Direct `dp.feed_update` and custom feed paths would lose the context | R23; 03 §5 names `feed_update` as the boundary |
| One `ContextVar.set` per stage (router, handler, phase) | Adds per-stage cost on the hot path; attribute writes on one per-update object are enough | D63 zero-cost intent |
| `LoggerAdapter` with `extra` | User loggers can't attach the context; a filter can be reused by users | D65 |
| Keys set only "where known" (absent otherwise) | `%(aiogram_update_id)s` in a format string raises on records outside updates | D65 |

## Validation

```bash
uv sync --locked --all-extras --group dev --group test
make dev            # once B-01 has landed; before that `uv sync` is enough (pure Python)
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Lands early (PD-31) on the 3.x-derived dispatcher. E-02 (executor) writes router/handler/phase, and E-14 keeps
  the `feed_update` boundary when it rewrites the feed paths.
- H-02 extends the factory with the redaction filter. Keep the factory signature stable.
- H-06 reuses the stable handler name (qualname; `<lambda>` gets a registration-site name) for `aiogram_handler`.
  Until H-06 lands, `aiogram_handler` uses the callback's `__qualname__`.

## Notes
