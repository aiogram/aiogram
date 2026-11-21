# Fix: webhook dispatch is missing the `dispatcher` context argument

## Why

Filters and handlers that declare a `dispatcher: Dispatcher` parameter work
under long polling but crash with `TypeError` when the same update arrives via
webhook. `start_polling` injects `"dispatcher": self` (and `"bots"`) into the
workflow kwargs (`aiogram/dispatcher/dispatcher.py:586-591`), but the webhook
request handlers pass only their constructor extras into
`feed_raw_update`/`feed_webhook_update`, so `dispatcher` never reaches the
handler context.

The failure is nasty in practice (confirmed community report, reproduced in
`mre/main.py` + `mre/simulate.py`):

- the `TypeError` is raised at filter-check time, so it aborts propagation for
  the whole event — sibling handlers registered after the broken one also never
  run;
- with `handle_in_background=True` (the default) the exception disappears into
  a detached task ("Task exception was never retrieved") — silent failure;
- with `handle_in_background=False` it surfaces as HTTP 500, causing Telegram
  to re-deliver the update.

## What Changes

`Dispatcher.feed_update` injects `dispatcher` into the contextual data, making
it available to filters, middlewares and handlers on **every** feed path
(polling, `SimpleRequestHandler`/`TokenBasedRequestHandler` webhook feeding,
`feed_raw_update`, `feed_webhook_update`, and direct `feed_update` calls —
including tests). Explicit overrides via kwargs or workflow data keep
precedence.

`bots` stays polling-only: a webhook request knows only the single bot that
received the update, so promising `bots` there would be a lie.

- Affected capability: `event-dispatching` (Requirement: Contextual data
  injection)
- Affected code: `aiogram/dispatcher/dispatcher.py` (`feed_update`)
- User-visible: bugfix changelog fragment required

## Impact

- Existing polling users: no behavior change (`dispatcher` was already there;
  the same object is injected).
- Webhook users: filters/handlers taking `dispatcher` start working instead of
  silently killing the event pipeline.
- Anyone calling `feed_update` directly (e.g. in tests): `dispatcher` becomes
  available without wiring it manually.
