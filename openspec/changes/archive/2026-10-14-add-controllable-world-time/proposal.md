## Why

The Bot API attaches documented time limits to several things `aiogram.test` already
models:

- mutes and bans expire;
- polls close on schedule;
- live locations stop being editable;
- old messages cannot be deleted, and old business messages cannot be edited;
- a pre-checkout query must be answered within 10 seconds, and an ephemeral command within
  15.

The toolkit has no clock a test can move, so none of these limits can be tested, and a bot
that mishandles one passes every test.

The toolkit's dates come from an update counter: each update adds one synthetic second.
That clock cannot be used to enforce a limit, because the outcome would depend on how many
unrelated updates a test happened to feed. It also measures an `until_date` given as a
`timedelta` from a fixed date instead of from "now".

## What Changes

- **A controllable clock.** World time stands still unless the test moves it with
  `await env.advance_time(...)`, which takes seconds or a `timedelta`. Advances never
  overlap. Every date the world assigns to something happening now is the clock's time.
  Updates no longer tick the clock.
- **Mutes and bans expire.** `until_date` is resolved against the clock, and the "less than
  30 seconds or more than 366 days means forever" rule applies. Once the clock reaches
  `until_date`, every membership read shows the restriction ended: a present restricted
  member is a member again, and an absent one or a banned user has left.
- **Polls close on schedule.** `open_period` or `close_date`, never both, are validated to
  be 5 to 2628000 seconds ahead and reported on the poll. When the clock reaches that point
  the poll and its message close, the bot receives a `poll` update, and voting is refused.
- **Live locations expire.** `editMessageLiveLocation` fails in three cases: once
  `live_period` has elapsed since the message was sent, after `stopMessageLiveLocation`, or
  on a location that was never live. A "forever" location (`0x7FFFFFFF`) is the exception.
  A new period is validated against the documented limits, with forever always allowed.
- **Message age limits.** `deleteMessage` fails for a message 48 hours old or older, and
  for a dice in a private chat that is 24 hours old or younger. `deleteMessages` skips such
  messages. Editing a business message the bot did not send, carrying no inline keyboard,
  fails after 48 hours through any of the four message edit methods.
- **Answer windows.** A pre-checkout answer fails once more than 10 seconds have passed
  since the query. A reply to an ephemeral command fails once more than 15 seconds have
  passed since the command.

Observable behavior changes in three places:

- dates no longer advance by a second per update;
- a `timedelta` `until_date` is measured from the clock;
- an `until_date` under 30 seconds or over 366 days is stored as "forever".

The toolkit is in alpha.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`:
  - Gains six requirements. They cover the controllable clock, expiring restrictions,
    scheduled poll closing, live location expiry, message age limits, and the ephemeral
    reply window.
  - Modifies "Outstanding queries are tracked and answers validated", where a pre-checkout
    query now expires after 10 seconds.
  - Modifies "Polls are world state", where the scheduled close is now stored.

## Impact

- **Code**:
  - `aiogram/test/world.py`: the clock, settling expired memberships, query issue times,
    and the poll close moment.
  - `aiogram/test/environment.py`: `advance_time` and its queue.
  - `aiogram/test/modeling.py`: the date helpers, poll scheduling, live location, deletion,
    business edit and answer-window checks.

  No generated code changes.
- **Tests**: `tests/test_testing/` gains one test module for time. Two existing tests
  change: the counter test in `test_world.py` and `test_ban_accepts_a_timestamp`.
- **Docs**: a "Time" section in `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: after `report-restricted-membership-truthfully`, which provides `is_member`,
  the status helper and the epoch reading of "forever". The ephemeral reply window also
  needs `model-ephemeral-messages`; the other limits do not.
- **Considered and left out**: these are listed in design.md with the reason for each.
  - Invite link expiry: joining by link is not modeled.
  - Subscription renewal: needs a renewal charge model.
  - The 24-hour "active chat" rule for business reads and gift transfers: Telegram does
    not define "active".
  - Chat actions: they leave no stored state.
  - Callback and inline answer timeouts, and ephemeral message lifetime: not documented.
  - Join-request query windows: these queries are not modeled.
