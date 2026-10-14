## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- `World.next_date()` returns `BASE_DATE + last_update_id` seconds. Every producer of a
  "now" date calls it: actors, modeled sends, service messages, star transactions, topic
  creation, and the synthesis context.
- `_as_datetime` resolves `until_date` and invite-link `expire_date` alike. It maps a
  `timedelta` to `BASE_DATE + delta` and an `int` to a Unix time, and passes a `datetime`
  through, naive or not.
- After `report-restricted-membership-truthfully`:
  - restricted users carry `is_member`;
  - one helper changes a member's status and clears `until_date` outside restricted and
    banned;
  - a missing end reads as the Unix epoch.
- `ChatState.member(user_id)` is the single accessor for a membership. Handlers, actors and
  tests all go through it.
- Polls are `PollState` objects. `stopPoll` closes one and updates the stored message's
  poll. Voting in a closed poll raises in the actor. `sendPoll`'s `open_period` and
  `close_date` are ignored.
- `stopMessageLiveLocation` clears `live_period`, and its docstring calls the fake "a fake
  with no clock". `editMessageLiveLocation` succeeds on any location.
- `World.pending_queries` maps a query id to its kind. `answer_query` raises the "query is
  too old ..." wording for a query that is not pending.
- Each `env.feed` opens its own route scope unless it runs inside `env.trigger()`.
- The docs recommend `looptime` for tests whose bot sleeps on the event loop. That clock is
  the loop's, and is unrelated to world dates.

## Goals / Non-Goals

**Goals:**

- One clock, moved only by the test, that every limit is measured against.
- Expiry that needs no background task and no polling, so a test stays deterministic
  between its own steps.

**Non-Goals:**

- Freezing or patching the host's time (`datetime.now`, `time.time`, `loop.time`) for the
  bot's own code or for wait timeouts. A bot that reads the wall clock itself is outside the
  world. The docs point to `time-machine`, and to `looptime` for event-loop sleeps, and say
  that neither moves the world clock and vice versa.
- Invite link `expire_date` and `member_limit` enforcement: joining by link is not modeled.
  Expiry has nothing to act on until it is.
- Subscription expiry and renewal (`subscription_period`): renewal is a recurring charge
  the star ledger does not model.
- The 24-hour "active chat" rule of `readBusinessMessage` and `transferGift`: the Bot API
  does not define "active".
- `sendChatAction`'s 5-second status: it leaves no world state to expire.
- Answer timeouts for callback and inline queries, and ephemeral message lifetime: the Bot
  API documents neither. The join-request query's 10-second window is documented, but
  join-request queries are not modeled; it joins D7 when they are.
- `chat_member` updates when a restriction or ban expires: the Bot API does not document
  them, so none are dispatched (D4).

## Decisions

### D1. Time starts at the real time and then stands still

`World` keeps `now`, exposed as `env.now`. `next_date()` returns it unchanged, and only
`advance_time` moves it.

It starts at the real time, to the second, unless the test passes `clock_start` (or
`Blueprint.build(start=...)`). A fixed start such as `BASE_DATE` was tried first and broke
bots that compute dates from the real clock, which is most of them:

- `sendPoll(close_date=datetime.now() + 5 min)` was refused as months ahead of the world;
- `until_date=datetime.now() + 1 h` landed months ahead, and from a year after `BASE_DATE`
  on it would silently become "forever", a test that starts failing on its own.

Telegram's clock is the real one, so the world's starts there. Reproducible dates stay one
argument away: `clock_start=BASE_DATE`. Declared topics are dated at the start, not at
`BASE_DATE`, so a declared world is not born months old.

The tick was there to make dates distinct. Nothing in the toolkit orders by date: messages
are ordered by id, updates by update id, star transactions by list order, administrators
by status and id. A ticking clock would make every limit depend on how many unrelated
updates a test fed. Ten button clicks between a pre-checkout query and its answer would
expire it. Removing the tick breaks one toolkit test, the counter test in
`test_world.py`.

*Alternative considered:* keep the tick and measure limits against a separate "explicit
time". Two clocks would put dates on messages that disagree with the clock the limits use,
and "how old is this message" would have two answers.

### D2. `advance_time` runs a due-event queue, one call at a time

`await env.advance_time(seconds | timedelta) -> None`:

1. Refuses a negative amount (`ValueError`), and a call while another advance is running,
   whether from a re-entrant handler or a concurrent task (`RuntimeError`). The clock stays
   unchanged.
2. Loops while the queue holds an event due at or before the target. It pops the earliest
   (ties broken by scheduling order), moves `now` to that event's moment, and dispatches
   it. Events scheduled during dispatch join the queue, so one that falls before the target
   fires within the same call.
3. Sets `now` to the target.

Events enter the queue through `env.schedule(moment, action)`, which the poll handler
uses and a test may use too. All dispatches of one call share one route scope
(`env.trigger()`), like a multi-update trigger. If a handler raises, the exception propagates, the clock stays at that event's
moment, and later events stay queued. Today only scheduled poll closing enqueues events.

### D3. Expiry is settled when a membership is read

`ChatState.member()` settles an expired restriction or ban before returning it, using its
world's `now`. Through the status helper from `report-restricted-membership-truthfully`,
a present restricted user becomes `MEMBER` and an absent one or a banned user `LEFT`, with
`until_date` cleared. Every reader goes through that accessor, so `getChatMember`, actors and
tests' own `chat.member(...)` all see the same answer. The member count reads
`chat.present_members()`, which settles each member through the same accessor.

Live locations, message age, and query and command windows are compared against `now` at
use. Nothing is rewritten in the background, so D2's queue holds only events that have to
produce an update.

*Alternative considered:* compute an "effective" view on every read and keep stored state
untouched. Every reader would need the clock passed in (`as_chat_member` has none), and a
test reading `chat.member(...)` would see a different status from the bot.

### D4. No membership update is dispatched when a restriction ends

The Bot API documents no `chat_member` update for an expiring restriction or ban.
Dispatching one would invent traffic that a bot could start depending on in tests and never
receive in production. If Telegram is shown to send one, adding it to D2's queue is a
contained change.

### D5. Two date helpers: resolve, then normalize `until_date`

- `resolve_date(value, now)` turns a `timedelta` into `now + delta`, an `int` into a Unix
  time, and a naive `datetime` into an aware one, the way aiogram's serializer does
  (`value.timestamp()`). An aware `datetime` passes through. It serves `until_date`,
  `close_date` and invite-link `expire_date`, replacing `_as_datetime`.
- `normalize_until(date, now)` applies the "less than 30 seconds or more than 366 days
  means forever" rule and returns `None` for forever. It is used for `until_date` only, so
  invite-link dates are never turned into "forever".

### D6. Polls schedule their close

`sendPoll` validates the schedule and refuses `open_period` together with `close_date`. It
stores the close moment on the `PollState`, which reports it as the `Poll`'s
`open_period`/`close_date`, and enqueues a close event. When the event fires on an open
poll, the close goes through the same code `stopPoll` uses, which also updates the stored
message, and then a `poll` update is dispatched. A poll already stopped is skipped.

### D7. Answer windows

- `World.query_issued` keeps the clock time at issue next to `pending_queries`.
  `answer_query` enforces the windows in `ANSWER_WINDOWS`, which holds the 10-second
  pre-checkout limit only.
- The 15-second ephemeral reply window compares the incoming command's `date` with `now`
  in the reply validation that `model-ephemeral-messages` adds.

### D8. Error wording is observed, not documented

The Bot API documents none of these strings. Where Telegram's wording is widely observed,
it is used:

- "query is too old ..." for a late pre-checkout answer;
- "message can't be deleted" for deletion;
- "message can't be edited" for live locations and business edits.

Out-of-range poll and live periods and a late ephemeral reply use the toolkit's own
`Bad Request: ...` text. The docs tell tests to assert the exception type, not the text.

## Risks / Trade-offs

- [Equal dates where tests previously saw increasing ones] → Nothing in the toolkit orders
  by date. A user test asserting increments was asserting an artifact. Called out in the
  changelog.
- [A fresh dice in a private chat can no longer be deleted] → That is the documented rule.
- [Settling on read mutates state inside an accessor] → It happens only for a restriction
  whose end has passed, and it is idempotent. The alternative leaves two answers to "what
  is this member's status".
- [The poll-close `poll` update, batch deletion skipping protected messages, and
  `until_date` ignored in basic groups are the toolkit's readings] → The Bot API covers
  each only indirectly. The docs label them as readings.

## Migration Plan

None at runtime. Tests that asserted per-update date increments change expectation. So
does `test_ban_accepts_a_timestamp`, whose `until_date=0` is now "forever": it reads back
as the epoch, but is stored as no end.
