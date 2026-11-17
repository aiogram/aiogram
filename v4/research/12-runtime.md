# 12 — Runtime: Runner, update sources, multi-bot

Polling and the webhook move out of `Dispatcher`. `Dispatcher` keeps only routing (`feed_update`,
`feed_raw_update`, the routers and their `DispatchTable` compilation from 03). Each Runner routes on its own
immutable snapshot (D114), so one `Dispatcher` can be shared across threads.
Everything that is bound to a loop or tied to a process lifecycle moves into a `Runner`, and transports become
**update sources** attached to it. The 3.x methods on `Dispatcher` stay as thin wrappers.

## Decisions

| # | Decision |
|---|---|
| **D21** | **One `Runner` per loop, with sources.** The Runner owns startup/shutdown, signals, in-flight task tracking, the concurrency limit, graceful shutdown and the bot registry. `Poller`, the webhook handlers and user-defined sources plug into it through a small protocol. Polling and webhook can mix in one process with a single startup/shutdown. |
| **D22** | **Bots are added and removed at runtime**, in both polling and webhook. There are no "move" semantics (no cross-process hand-off and no polling↔webhook switch). Removal confirms **admitted** updates and doesn't replay them (reworded by R13, see 19). A crash or a shutdown deadline may lose or replay work, so delivery stays **best-effort, not exactly-once**. |
| **D23** | **No Rust web server** (05 §3 reaffirmed). aiogram ships the aiohttp adapter and an ASGI app on the same core; Granian is documented for users who want a Rust HTTP server. |
| **D24** | **Webhook bot lookup keeps the 3.x approaches**: `SimpleRequestHandler` (one bot, secret token) and `TokenBasedRequestHandler` (token in the path, bot created on demand). Both become Runner sources. |

## 1. Today

`Dispatcher` (741 lines) mixes routing with lifecycle: `_running_lock`, `_stop_signal`, `_handle_update_tasks`,
signal handlers, `start_polling` (`dispatcher.py:568`), the `getUpdates` loop with backoff (`:203-258`), and the
webhook reply-or-background timeout logic (`feed_webhook_update`, `:470-529`). The webhook has its own lifecycle
in `setup_application` (`webhook/aiohttp_server.py:23`), so startup/shutdown is emitted from two places. Bots
are fixed at start (`bots` tuple, `:641`). The concurrency limit and shutdown timeout exist only for polling.

## 2. Layers

```
Dispatcher (mutable, thread-shared)     routing only: feed_update / feed_raw_update
   ▲
Runner (one per loop)                   routing snapshot (D114), lifecycle, signals, task set, admission, shutdown timeout,
   │                                    bot registry, workflow data, per-update isolation (10)
   ├── Poller                           getUpdates loop per bot, backoff, allowed_updates, offset commit
   ├── SimpleRequestHandler / TokenBasedRequestHandler   (aiohttp adapter)
   ├── ASGI app                         same webhook core, raw bytes in → status + bytes out (05 §2.4)
   └── user source                      e.g. a Redis Streams / Kafka consumer
```

```python
runner = Runner(dp, handle_signals=True, tasks_concurrency_limit=100, tasks_shutdown_timeout=30)
poller = runner.attach(Poller(polling_timeout=10, allowed_updates=UNSET))
await runner.add_bot(bot_a, source=poller)
async with runner:                       # startup → serve → shutdown
    await runner.add_bot(bot_b, source=poller)   # any time
    await runner.remove_bot(bot_a)
    await runner.wait_closed()
```

## 3. Runner

- **Feed entry points for all sources (R12)**: `runner.feed(bot, raw: bytes | Update)` **admits** the update: it
  awaits capacity, then schedules processing, so awaiting it guarantees admission, not completion.
  `runner.process(bot, raw) -> TelegramMethod | None` runs inline and returns the handler's reply method for
  sources that can answer inline (webhook). Both decode in the core, track tasks and isolate per-update errors (10).
  Webhook therefore gains `tasks_concurrency_limit` / `tasks_shutdown_timeout` for free.
- **Routing snapshot (D114)**: compiled at start; changes to routers after start apply on restart or
  `runner.refresh()`, with a one-time warning when someone mutates a graph the running snapshot references.
  `runner.stop()` drains and closes; nothing raises on late registration.
- **Lifecycle**: `dp.startup` / `dp.shutdown` are emitted exactly once per Runner, whatever the number of sources.
  SIGINT/SIGTERM are handled once, and only by the main-thread Runner (R12).
- **Per-bot hooks (new)**: `dp.bot_added` / `dp.bot_removed` observers fire for every bot, including the ones
  present at start (after `startup`, before `shutdown`). This is where per-bot setup lives (`set_my_commands`,
  `set_webhook`). 3.x startup code that loops over `bots` keeps working.
- **Bot registry**: an ordered read-only sequence. The `bots` value in startup/handler data is the cached tuple,
  rebuilt on add/remove, so there's no per-update cost and the 3.x `bots[-1]` style still works.
- **Workflow data**: `Runner(dp, **kwargs)` merges with `dp.workflow_data` as `start_polling(**kwargs)` does today.
- **Free-threading** (07): one Runner per thread/loop and one shared `Dispatcher`. `run_polling_threads` becomes
  N Runners with bots sharded across them. A single high-traffic bot gets one ingress poller that hands updates
  off to the Runners sharded by isolation key (07 §1, R12).

## 4. Source protocol

```python
class UpdateSource(Protocol):
    async def start(self, runner: Runner) -> None: ...
    async def stop(self) -> None: ...                     # stop receiving; Runner drains tasks
    async def add_bot(self, bot: Bot) -> None: ...
    async def remove_bot(self, bot: Bot) -> None: ...
```

The protocol is deliberately small. Sources call `runner.feed(...)` / `runner.process(...)` and never touch tasks
or the dispatcher.

## 5. Poller

- One `getUpdates` task per bot, with today's backoff and logging, and the `request_timeout = session.timeout +
  polling_timeout` rule (`dispatcher.py:218-221`).
- `allowed_updates=UNSET` is resolved from `dp.resolve_used_update_types()` at source start.
- **Remove a bot**:
  1. Cancel its long-poll.
  2. Commit the offset with `getUpdates(offset=last_admitted_id + 1, timeout=0, limit=1)`. Telegram confirms an
     offset only on the *next* call, so without this step the last batch is delivered again when the bot is
     re-added or polled elsewhere. Updates returned by this `limit=1` call are ignored and stay unconfirmed (R13).
  3. Wait for its in-flight tasks up to `tasks_shutdown_timeout`, then cancel them.
  4. Emit `bot_removed`.
  5. Close the session if the Runner owns it (`add_bot(..., close_session=True)`, the default, as
     `close_bot_session` is today).
- **409 Conflict** (another poller or a webhook is active): keep retrying with backoff as today, but log it as
  that specific cause. No automatic `deleteWebhook` (unchanged).

## 6. Webhook

- `SimpleRequestHandler` and `TokenBasedRequestHandler` stay as the two ways to pick the bot (D24). They become
  sources: `handler.register(app, path)` plus `runner.attach(handler)`; `setup_application(app, dp)` builds the
  Runner and hooks it to aiohttp startup/cleanup.
- `TokenBasedRequestHandler` registers a bot it creates on demand through `runner.add_bot`, so `bot_added` fires
  for it as well.
- The reply-or-background logic (answer inline within ≈55 s, otherwise continue in the background and call the
  method) moves from `Dispatcher.feed_webhook_update` into the shared webhook core used by both aiohttp and ASGI.
  Background tasks are tracked by the Runner, so shutdown waits for them. This fixes the dropped-on-shutdown bug.
  Background mode has a pending cap (`max_pending`); beyond it the handler answers 5xx so Telegram redelivers (R12).
- Replies are JSON for methods without files and multipart otherwise (R18, 05 §2.4).
- Body read as bytes → `runner.process(bot, raw)` (05 §2.4).

## 7. Backward compatibility

| 3.x | 4.0 |
|---|---|
| `dp.start_polling(*bots, polling_timeout=, handle_as_tasks=, backoff_config=, allowed_updates=, handle_signals=, close_bot_session=, tasks_concurrency_limit=, tasks_shutdown_timeout=, **kw)` | wrapper: `Runner(dp, …)` + `Poller(…)` with those bots; same signature |
| `dp.run_polling(...)` | same wrapper plus `asyncio.Runner` / uvloop as today |
| `dp.stop_polling()` | stops the Runner started by this dispatcher's `start_polling`; `RuntimeError` if none (as today) |
| `dp.feed_webhook_update(bot, update)` | kept; delegates to the webhook core |
| `dp.feed_update` / `feed_raw_update` | unchanged (routing only); without a Runner they compile and cache a snapshot keyed by a topology epoch (D114) |
| `setup_application(app, dp, **kw)`, `SimpleRequestHandler`, `TokenBasedRequestHandler` | kept; built on Runner |

There are no new breaking changes. `bot_added` / `bot_removed` and runtime `add_bot` / `remove_bot` are additions.

## 8. Rejected

- **Each source owning its own lifecycle**: mixing polling and webhook would emit startup/shutdown twice and
  duplicate signal handling.
- **Move semantics** (cross-process hand-off, polling↔webhook switch): not requested (D22). The offset commit on
  remove is the piece a future hand-off would build on.
- **Rust web server** (D23): about 60–70 µs per request for aiohttp against a thread hop each way into asyncio,
  plus a tokio runtime that `fork` does not survive. Granian over the ASGI app covers the need.
