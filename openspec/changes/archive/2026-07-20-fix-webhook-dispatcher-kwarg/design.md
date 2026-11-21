# Design

## Root cause

Two entry points build handler context differently:

- Polling: `Dispatcher._run_polling` builds
  `workflow_data = {"dispatcher": self, "bots": bots, **self.workflow_data, **kwargs}`
  and threads it down to `feed_update` (`dispatcher.py:586-591`).
- Webhook: `BaseRequestHandler._handle_request[_background]` calls
  `dispatcher.feed_raw_update(bot=bot, update=update, **self.data)` where
  `self.data` is only the extras the user passed to the handler constructor.

`feed_update` itself merges `{**self.workflow_data, **kwargs, "bot": bot}` —
nothing adds `dispatcher`, so it exists only on the path that happened to
inject it.

## Decision: inject in `feed_update`, not in the webhook handlers

Fix at the single choke point every feed path routes through:

```python
response = await self.update.wrap_outer_middleware(
    self.update.trigger,
    update,
    {
        "dispatcher": self,
        **self.workflow_data,
        **kwargs,
        "bot": bot,
    },
)
```

Precedence (first is weakest): injected `self` → `workflow_data` → explicit
`kwargs`. This mirrors `start_polling`'s existing dict order, so polling
behavior is bit-for-bit unchanged (same object, same overridability), and a
caller who deliberately passes `dispatcher=...` still wins.

Rejected alternative: adding `dispatcher` to `BaseRequestHandler.data` in
`aiogram/webhook/aiohttp_server.py`. It fixes only the aiohttp handlers and
leaves direct `feed_update`/`feed_raw_update` callers (custom web frameworks,
tests) with the same polling/webhook asymmetry.

Out of scope: `bots` remains polling-only workflow data; a webhook process
serves one bot per request and cannot enumerate the fleet.

## Failure-mode note (why the bug was silent)

The `TypeError` fires inside `HandlerObject.check` → `CallableObject.call`
during filter evaluation, i.e. outside any user `try/except` in the filter
body. In background webhook mode the exception ends in a detached task and is
never retrieved. No change to that machinery is needed once the argument is
supplied, but the regression test must cover the webhook HTTP path end-to-end
to lock the contract, not just `feed_update` kwargs.

## Testing

- Unit: a filter and a handler declaring `dispatcher` receive the `Dispatcher`
  instance via plain `feed_update` (no extra kwargs).
- Regression (webhook): POST an update through `SimpleRequestHandler` (both
  `handle_in_background` modes) with a state-dependent filter requiring
  `dispatcher`; assert the filtered handler fires and no task exception leaks.
- Override: passing `dispatcher=sentinel` to `feed_update` reaches the handler
  unchanged.
