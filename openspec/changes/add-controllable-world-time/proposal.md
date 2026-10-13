## Why

The Bot API attaches documented time limits to several things `aiogram.test` already
models: mutes and bans expire, polls close on schedule, live locations stop being editable,
old messages cannot be deleted, a pre-checkout query must be answered within 10 seconds,
and an ephemeral command must be answered within 15. The toolkit has no clock a test can
move, so none of these limits can be tested, and a bot that mishandles one passes every
test.

The toolkit's dates come from an update counter: each update adds one synthetic second.
That clock cannot be used to enforce a limit, because the outcome would depend on how many
unrelated updates a test happened to feed. It also contradicts the docs in two places:
an `until_date` given as a `timedelta` is measured from a fixed date instead of from
"now", and a mute or ban "forever" is reported with that fixed date instead of Telegram's
`0`.

## What Changes

- **A controllable clock.** World time stands still unless the test moves it with
  `await env.advance_time(...)`, which takes seconds or a `timedelta`. Every date the world
  produces is the clock's current time. Updates no longer tick the clock.
- **Mutes and bans expire.** `until_date` is resolved against the clock. Telegram's
  "less than 30 seconds or more than 366 days means forever" rule applies, and "forever" is
  reported as `0`. Once the clock passes `until_date`, membership reads show the
  restriction lifted: a restricted member is a member again, and a banned user has left.
- **Polls close on schedule.** `open_period` and `close_date` are validated to be 5 seconds
  to 30 days ahead and stored. When the clock passes that point the poll closes, the bot
  receives a `poll` update, and voting is refused as it is for a stopped poll.
- **Live locations expire.** `editMessageLiveLocation` fails once `live_period` has elapsed
  since the message was sent, unless the period is "forever" (`0x7FFFFFFF`). A new
  `live_period` is validated against the documented limits: at most a day more than the
  current one, and expiring within 90 days.
- **Message age limits.** `deleteMessage` fails for a message older than 48 hours, and for
  a dice in a private chat younger than 24 hours. `deleteMessages` skips such messages.
  Editing a business message that the bot did not send and that has no inline keyboard
  fails after 48 hours.
- **Answer windows.** `answerPreCheckoutQuery` fails once 10 seconds have passed since the
  query. A reply to an ephemeral command fails once 15 seconds have passed since the
  command.

Observable behavior changes in three places:

- Dates no longer advance by a second per update.
- "Forever" restrictions report `until_date` as `0`.
- A `timedelta` `until_date` is measured from the clock.

All three earlier behaviors were wrong, and the toolkit has not been released.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains seven requirements. They cover the controllable clock,
  expiring restrictions, scheduled poll closing, live location expiry, message age limits,
  the pre-checkout answer window, and the ephemeral reply window. No existing requirement
  text changes: none of them specifies dates.

## Impact

- **Code**: `aiogram/test/world.py` (the clock, time-aware membership reads, query issue
  times), `aiogram/test/environment.py` (`advance_time`), and `aiogram/test/modeling.py`
  (`until_date` resolution, poll scheduling, live location, deletion, business edit and
  answer-window checks). No generated code changes.
- **Tests**: `tests/test_testing/` gains one test module for time. `test_world.py`'s
  counter test changes, because dates no longer tick per update.
- **Docs**: a "Time" section in `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: after `model-ephemeral-messages`, which the ephemeral reply window builds on.
  The other limits do not depend on it.
- **Considered and left out**: these are listed in design.md with the reason for each.
  - Invite link expiry: joining by link is not modeled.
  - Subscription renewal: needs a renewal charge model.
  - The 24-hour "active chat" rule for business reads and gift transfers: Telegram does
    not define "active".
  - Chat actions: they leave no stored state.
  - Callback and inline answer timeouts, and ephemeral message lifetime: not documented.
