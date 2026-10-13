## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- `World.next_date()` returns `BASE_DATE + last_update_id` seconds. Every producer of a
  date calls it: actors, modeled sends, service messages, star transactions.
- `_as_datetime` resolves `until_date`. It maps a `timedelta` to `BASE_DATE + delta`, and
  `MemberState.as_chat_member` reports a missing `until_date` as `BASE_DATE`.
- Polls are `PollState` objects. `stopPoll` closes them, and voting in a closed poll raises
  in the actor. `sendPoll`'s `open_period` and `close_date` are ignored.
- `stopMessageLiveLocation` clears `live_period`, and its docstring calls the fake "a fake
  with no clock".
- Outstanding queries live in `World.pending_queries` (id to kind). `answer_query` raises
  Telegram's "query is too old ..." wording for a query that is not pending.
- After `model-ephemeral-messages`, incoming ephemeral commands are stored per chat with
  their `date`.

## Goals / Non-Goals

**Goals:**

- One clock, moved only by the test, that every limit is measured against.
- Expiry that needs no background task and no polling, so a test stays deterministic and
  synchronous between its own steps.

**Non-Goals:**

- Freezing or patching the host's time (`datetime.now`, `time.time`) for the bot's own
  code. A bot that reads the wall clock itself is outside the world. This stays the job of
  a tool such as `time-machine`, and the docs say so.
- Invite link `expire_date` and `member_limit`: joining by link is not modeled, so expiry
  would have nothing to act on. It becomes relevant when link joining lands.
- Subscription expiry and renewal (`subscription_period`): renewal is a recurring charge
  the star ledger does not model.
- The 24-hour "active chat" rule of `readBusinessMessage` and `transferGift`: the Bot API
  does not define "active".
- `sendChatAction`'s 5-second status: it leaves no world state to expire.
- Answer timeouts for callback and inline queries, and the lifetime of ephemeral messages:
  the Bot API documents neither.
- `chat_member` updates when a restriction or ban expires: the Bot API does not document
  them, so none are dispatched (D4).

## Decisions

### D1. Time stands still; updates no longer tick the clock

`World` keeps `now` (initially `BASE_DATE`). `next_date()` returns it unchanged, and only
`advance_time` moves it. The per-update second is dropped.

The tick was there to make dates distinct. Nothing reads dates for ordering: messages are
ordered by id and updates by update id. A ticking clock, on the other hand, makes every
limit depend on how many unrelated updates a test fed. Ten button clicks between a
pre-checkout query and its answer would expire it. A test can then not reason about time
at all.

*Alternative considered:* keep the tick and measure limits against a separate "explicit
time". Two clocks would put dates on messages that disagree with the clock the limits use,
and "how old is this message" would have two answers.

### D2. `advance_time` is async and fires due events in order

`await env.advance_time(seconds | timedelta)` validates the amount, moves `now`, and then
dispatches what became due, ordered by due moment and then by the order it was scheduled
in. Today only scheduled poll closing produces an update.

It is async because dispatching a `poll` update runs handlers. It moves the clock to each
event's moment before dispatching it, so a handler reacting to a poll closing sees that
moment as "now", not the final target.

### D3. Expiry is evaluated on read, not by mutation

A restriction's end, a live location's end, a message's age, and a query's or command's
window are compared against `now` when they are read or used. Nothing is rewritten when
time passes, so no scheduler entry is needed for them. That keeps D2's queue to the events
that have to produce an update.

Membership reads compute the effective status: a restricted member past `until_date` reads
as `member` with the chat's default permissions, and a banned user past it reads as
`left`. The stored `MemberState` keeps what was set, so `until_date` stays inspectable.

### D4. No membership update is dispatched when a restriction ends

The Bot API documents no `chat_member` update for an expiring restriction or ban.
Dispatching one would invent traffic that a bot could start depending on in tests and
never receive in production. If Telegram is shown to send one, adding it to D2's queue is
a contained change.

### D5. `until_date` is normalized once, at the call

`_as_datetime` resolves a `timedelta` against `now`, and an `int` as a Unix time. The
"less than 30 seconds or more than 366 days means forever" rule is then applied, and
forever is stored as `None`. `as_chat_member` reports `None` as `0` (the Unix epoch), which
the Bot API defines as forever, replacing the `BASE_DATE` placeholder. For bans,
`until_date` applies to supergroups and channels only; in a basic group a ban is always
forever, as documented.

### D6. Limits reuse Telegram's wording where it is known

- A late or unknown pre-checkout answer: the existing "query is too old ..." wording.
- Deleting a message that is too old, or a dice that is too young: "message can't be
  deleted".
- Editing an expired live location or an old business message: "message can't be edited".
- Out-of-range poll periods, a live period over the limits, and a late ephemeral reply:
  no documented wording, so the toolkit's own `Bad Request: ...` text is used, one place
  each.

### D7. Query issue times live next to the pending map

`pending_queries` keeps the clock time at issue alongside the kind. `answer_query` checks
the window only for pre-checkout queries, the one kind with a documented limit. The other
kinds keep today's "answer once" behavior with no expiry.

## Risks / Trade-offs

- [Equal dates where tests previously saw increasing ones] → Nothing in the toolkit orders
  by date. A user test asserting `date` increments was asserting an artifact. Called out in
  the changelog.
- [A fresh dice in a private chat can no longer be deleted] → That is the documented rule.
  A test that relied on the old behavior was testing behavior Telegram rejects.
- [Inferring `left` for an expired ban] → The Bot API says the user "will be unbanned".
  An unbanned user who is not in the chat is `left`, which is what `unbanChatMember`
  already produces in the toolkit.
- [The poll-close `poll` update is inferred from "bots receive updates about polls sent by
  the bot"] → A closing changes the poll's state, which that sentence covers. Stated in the
  docs as the toolkit's reading.

## Migration Plan

None at runtime. Tests that asserted per-update date increments, or `BASE_DATE` as a
"forever" `until_date`, change their expectation.
