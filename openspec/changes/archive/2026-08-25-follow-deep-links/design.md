## Context

`click()` earns its keep by validating: it refuses to press a button that is not there, so a
test that renames its callback data fails loudly instead of exercising a handler nobody can
reach. A deep-link button deserves the same guarantee — and needs more, because "following" it
is not one action but a small simulation of what a Telegram client does.

What a client does with `t.me/<bot>?start=<payload>` is well-defined and simple: open a private
chat with that bot and send `/start <payload>`. What it does with `?startapp=`, `?startgroup=`
or `t.me/<bot>/42` is well-defined and *not simple*, and none of it is anything this toolkit
simulates.

## Goals / Non-Goals

**Goals:**

- The button must be real, exactly as for `click()`.
- Following replays what tapping causes, through the ordinary machinery — no special-cased
  update.
- A kind the toolkit does not simulate is refused by name, with a reason a reader can act on.

**Non-Goals:**

- **Simulating Mini Apps, choosers or the attachment menu.** Each is a client flow with its own
  update types, and pretending otherwise is worse than refusing.
- Following a link to another bot. There is no other bot in the world to receive it.
- Modelling the deep-link *payload* semantics. The payload is handed to the bot as the `/start`
  argument, which is exactly what Telegram does; what it means is the bot's business.
- Joining a chat from an invite link. The membership triggers already cover that flow directly.

## Decisions

### D1. Following replays a `/start`, through an ordinary actor

`follow_deep_link` ends with `UserActor(self.environment, self.user).send(text)` — a fresh,
unbound actor for the same user. That is a decision, not an implementation detail: the flow
under test is "a message arrives in the DM", and routing it through the same `send()` a test
would write by hand means filters, middlewares, FSM and the command parser all see exactly what
they see in production. There is no deep-link-shaped update in the Bot API, and inventing one
here would be inventing a code path.

The text is `/start <payload>` when there is a payload and a bare `/start` when there is not,
which is what a client sends.

### D2. One table decides what each kind does

`_LINK_KINDS` maps a parsed kind to `(followable, rejection)`. The parser classifies by
iterating that table's keys; `follow_deep_link` and the automatic scan each do a single lookup
in it.

The first version had the classification in the parser, a set of followable kinds next to it,
and a bespoke `if` chain building the message — three things to keep in sync, and adding a kind
meant editing all three. Adding a kind is now a one-row change; two rows for a kind derived from
the path shape rather than a query parameter, and even that is derived: `_QUERY_PARAM_KINDS` is
the complement of `_PATH_DERIVED_KINDS` within the table, so the two cannot drift.

### D3. Refuse by name; never downgrade to a plain `/start`

The rejected reading is the tempting one: parse out the username, ignore the rest of the url,
send `/start`. It is tempting because it makes more tests pass, and it is wrong because the
tests it makes pass are testing a flow the bot does not have. A `startgroup` button opens a
group chooser; the bot's group flow is reached with `add_bot()`, and the rejection says so.

The same reasoning covers a query Telegram does not define — `?text=hi`, or anything else. The
honest answer is "what a real client does with this is not simulated", and it is its own kind
(`unknown_query`) with its own message, rather than being swept into either "followable" or
"not a deep link at all".

*Consequence:* a `start` parameter wins whenever it is present, alongside any other query
parameter, harmless (`utm_source=...`) or not — because a real client reads the parameter it
recognizes and ignores the rest.

### D4. A bare profile link is followable

`t.me/<username>` with no query parses as `start` with an empty payload, because that is what
tapping a profile link and pressing Start sends. Refusing it would be refusing the most common
link of all on a technicality.

### D5. The scan looks past what it cannot follow, and explains what it skipped

With no explicit target, the scan walks buttons newest-first and takes the first *followable*
link to this bot. A button targeting this bot with some other kind is remembered as a
*candidate* instead of ending the scan, so a keyboard mixing a Mini App button with a real
`start` link still finds the `start` link.

When only unfollowable candidates were found, the failure names each url and why it was
rejected — which is the difference between "no deep-link button here" and "four of them, none
followable, here's why". Buttons linking to another bot are simply skipped: they are not
candidates, since they were never this bot's to follow.

### D6. Path-derived kinds are rejected before the username is compared

For an invite link (`t.me/+hash`, `t.me/joinchat/hash`) or a url with extra path segments, the
parsed `username` is meaningless — `t.me/+abc` has no bot in it at all. Comparing it against the
bot's would produce "deep-links to @+abc, not to this bot", which points at the wrong problem.
These kinds are refused first, with a message about what the url *is*.

Membership in `_PATH_DERIVED_KINDS` is a property of the kind, so it is a frozen set rather than
a third field repeated on every row of the table.

### D7. A user's own private chat is opened on demand, not declared

This started as a deep-link requirement — the tap opens the DM — and generalized once stated.
Every Telegram user can open a private chat with any bot, so a blueprint that did not declare
one is not asserting its absence.

`World.ensure_private_chat(user)` builds it from `private_chat_shape`, the same description
`Blueprint.add_private_chat` uses, and registers it in the chat registry, which is what hands
the chat its world and therefore binds everything stored in it. Three entry points reach it: a
followed link, `UserActor.chat` for an unbound actor, and `in_()` when the target id is the
actor's own.

*The line is deliberate.* Any other undeclared chat still raises. The world cannot invent a
group's title, type or membership from a bare id, and a bot cannot post into a chat it was never
added to — so guessing there would hide a real setup error.

## Risks / Trade-offs

- **The policy encodes a reading of client behavior** → where the toolkit is unsure it refuses,
  which is recoverable (the test writes the `/start` itself) in a way a wrong simulation is not.
- **A future link kind arrives unlisted** → it falls into `unknown_query` and is refused with a
  message saying so, which is the safe direction. Adding it later is one row.
- **`ensure_private_chat` hides a typo** → `.in_(alice.id)` on a user whose chat was never
  declared now succeeds. Accepted: the id is the *user's own*, which the world already knows,
  so there is no undeclared entity being invented. A wrong id still raises, because it is not
  that actor's id.
- **Following returns the handler's value from a different actor** → the fresh actor is
  deliberately unbound, so the resulting update is a private message and not a group one. A test
  that wants the DM actor afterwards builds it the ordinary way.

## Migration Plan

Additive. The one behavior change is that `.in_(own id)` and `send()` from an unbound actor no
longer raise for an undeclared private chat.

## Open Questions

- Should `follow_deep_link` return the opened `ChatState` alongside the handler's return value?
  It returns the handler's value today, matching every other trigger; the chat is one
  `env.chat(user.id)` away.
