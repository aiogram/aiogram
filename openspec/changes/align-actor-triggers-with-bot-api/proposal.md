## Why

An audit of the actor triggers and the environment found updates that Telegram would never
deliver, or would deliver differently, and diagnostics that misreport what ran. Each finding
was reproduced. Examples:

- `click(..., message=m)` delivers a callback for a button that does not exist, or on a
  stale copy of a message the bot has since edited.
- A handler that raises `SkipHandler` is reported as the handler that ran.
- A user's edit carries no `edit_date`, and a user can edit the bot's own messages.
- `drain()` reports exceptions a bot already caught.
- A business connection update names whoever triggered it instead of the account owner.
- `update_subscription()` always sends a state value the Bot API does not allow.
- `inline_query()` never sets `chat_type`.
- `vote()` delivers several answers on a single-answer poll, and a changed answer where
  revoting is not allowed.
- `guest_message()` carries no `guest_query_id`, so the canonical answer handler crashes.

## What Changes

- **Clicks:** a click with an explicit message resolves that message's stored version and
  requires the button to be on it.
- **Routing diagnostics:** a handler that skips (`SkipHandler`) or cancels is not reported
  as the handler that ran.
- **User edits:** they carry `edit_date`, change only what the test passes, and are refused
  on a message the user did not send. A hand-fed edit updates the stored message instead of
  colliding with it.
- **`drain()`:** it reports only exceptions nobody retrieved.
- **Business connections:** connection updates name the account owner.
- **Subscriptions and payments:** `update_subscription(state=...)` takes the state, one of
  the documented values. `pay()` for a subscription sets its expiry date and the
  first-recurring flag.
- **Inline queries:** `inline_query()` carries `chat_type`, derived from the actor's chat.
- **Votes:** `vote()` refuses options the poll does not have, several options on a
  single-answer poll, and a changed vote where revoting is not allowed.
- **Guest messages:** `guest_message()` carries a `guest_query_id` the bot can answer,
  accepts `fields=`, and is registered like other carried messages.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains requirements for each point above. No existing
  requirement text changes.

## Impact

- **Code**: `aiogram/test/actors.py`, `aiogram/test/environment.py` and
  `aiogram/test/world.py`. No generated code changes.
- **Tests**: `tests/test_testing/` gains a regression test per finding, and tests that
  pinned the old behavior change.
- **Docs**: `docs/dispatcher/testing.rst` where it describes the affected triggers.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: independent of `align-fake-api-with-bot-api`. Vote validation reads the poll
  settings that change stores; it works today with the stored defaults.
