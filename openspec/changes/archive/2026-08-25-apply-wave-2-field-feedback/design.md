## Context

The first round of feedback found things that were missing or that raised. This round found
none of either. Every finding here is a place where the fake answered something a real
Telegram would never answer, plausibly enough that the bot's own code accepted it and the
test went green.

That changes what "correct" means for a fix. It is not enough for the toolkit to have *an*
answer for each of these; the answer has to be one the real API could have produced, or an
error the bot under test cannot mistake for one. Where those two are in tension — the chat
the world does not have — the error wins, loudly, because a wrong-but-plausible answer is the
failure mode this whole toolkit exists to avoid.

Several of the findings also turned out to be the *same* finding seen from different places:
two paths that should have shared a rule and did not. Those are fixed by making the rule one
thing, not by patching the second path to agree with the first.

## Goals / Non-Goals

**Goals:**

- No answer the real Bot API could not have given, on any path a bot reaches.
- A setup gap the bot's own `except` cannot swallow, with a message that says both how to
  declare the missing thing and how to test the branch it was mistaken for.
- One rule per question, at one place, rather than two paths that happen to agree today.
- Configuration a suite states once rather than on every call.

**Non-Goals:**

- Enforcing permissions. The couplings are about what `getChatMember` *reports*, not about
  what a later `sendMessage` is allowed to do; the toolkit still models the shape of
  administration and not its policy.
- Modelling the Mini App, group-chooser and attachment-menu flows. `start` winning over them
  is about reading a link the way a client reads it, not about simulating what they open.
- A fake clock. The `looptime` recipe is documentation of a composition that already works,
  not a dependency.

## Decisions

### D1. One rule for everything entering the world: `owned_or_copied`

A value a test hands the toolkit is one of two things, and they need opposite treatment. A
module-level `MENU` keyboard is the *caller's*: letting it into the world binds it to a bot
as the world mounts whatever it stores, so the constant stops comparing equal to its own
unbound twin for the rest of the session. A stored message passed as `reply_to_message` is
the *world's*: copying it hands back a snapshot that later edits to the original no longer
show through, and turns two fields that aliased one object into two unrelated copies.

Both halves already existed. `actors._detached` knew the rule for a trigger's `fields=`;
`derive_message` did not, and called `detached_copy` unconditionally. So
`send(fields={"reply_to_message": stored})` aliased and `edit(fields={"reply_to_message":
stored})` copied — the same line meaning two different things depending on the trigger
carrying it.

The rule is now `mounting.owned_or_copied(value, owner=..., bind=...)`, and both callers use
it. It lives in `mounting.py` because that module already owns both halves of the ownership
policy and the rule is nothing but their combination; leaving it in `actors.py` is what let
the second caller be written without it.

Ownership is compared by **identity** against the environment's bot, for the reason D3 of the
mounting change gives: two bots built from one blueprint compare equal, so `==` cannot answer
"whose is this". A value bound to some *other* bot is therefore copied, not passed through —
the exemption is ownership, not "already bound to something".

`bind=` exists because the two callers differ in what happens next. `derive_message` puts its
result straight into the world, so minting the copies already bound saves a second walk; a
trigger's fields are mounted as part of the whole update by `feed`, so there is nothing there
for early binding to save and the copies stay unbound.

### D2. `start` is checked first, not found by table order

Deep-link classification iterated `_QUERY_PARAM_KINDS`, the key order of the policy table.
`start` sits last there, so `?start=game-42&startapp=game-42` matched `startapp` and was
refused by name — a link a real client opens the bot with, and one Telegram itself hands out,
since a Mini App button carries both so that a client which cannot open the app still starts
a conversation.

The docstring already promised that `start` wins whenever it is present; only the code
disagreed. Iterating `("start", *_QUERY_PARAM_KINDS)` makes them agree, in either query
order, and costs one redundant lookup on links that have no `start`.

Precedence rather than a special case, because that is what a client does: it reads the
parameter it recognizes and ignores the rest of the query. Which also bounds the change —
the precedence needs a real `start` to take it, so `?startapp=abc` alone is refused exactly
as before. Every other kind is mutually exclusive in practice, so among *those* the table
order is a tie-break that never has to break a tie.

### D3. A chat's messages are sorted on insert, not on read

`chat.messages[-1]` is what every test in this toolkit's own documentation writes to mean
"the newest message". Almost every producer allocates its id from the chat and appends, so
the list is sorted — but not every one: `_register_carried_message` registers a message an
update carried in from *another* environment, and that id was allocated over there. Appending
it left the list unsorted for everything after, and `chat.messages[-1]` pointed at the older
message.

Sorting on read was rejected: `messages` is a plain list a test indexes, slices and asserts
the length of, and re-sorting it on every access would be both a cost on the hot path and a
lie about what the attribute is. `add_message` scans backwards from the end and inserts,
which costs one comparison in the overwhelming append case and is correct in the other.

The alternative of renumbering a carried message into this chat's own id space was rejected
too: the id is how a test correlates the message it fed with the message the world holds, and
changing it silently would break that correlation to fix a display order.

### D4. The newest match is the highest `message_id`

`wait_for_message` promised the newest match and delivered the last one in the list, by
scanning `reversed(view())` and returning the first hit. D3 makes that promise true again for
the ordinary case, but "the list is sorted" is not something a caller can act on, and the one
path that breaks it is exactly the one where a test asking for the bot's latest reply must
not silently get a stale one.

So the scan now evaluates **every** message and keeps the highest `message_id` among the
matches. It is the same order of work — the predicate already ran on every message up to the
first hit, and on all of them whenever there was no hit — and it makes the returned message
right by the same measure Telegram uses to say which message is newer.

The predicate-raised bookkeeping is unchanged and still per-pass, so a timeout still reports
what the predicate raised and on which message.

### D5. An undeclared chat on the outbound path raises, and opens nothing

`resolve_chat` answered `ApiRejection("chat not found")`, which `handle_call` turned into a
`TelegramBadRequest` carrying Telegram's own wording for it. That wording belongs to a real
situation — the user never opened the DM, or blocked the bot — and it is a situation bots
handle. So the bot's `except TelegramBadRequest` caught a missing blueprint declaration, ran
its blocked-user branch, and the test passed having exercised a branch it never meant to
reach. This was the one path in the toolkit still breaking its own two-kinds-of-failure rule.

It now raises `WorldLookupError` like every other undeclared thing. The message enumerates
the chats the world *does* have, with each one's type and readable name, because "chat -100
is not declared" is much less useful than the four lines showing that the test meant `-1001`.

**The outbound path deliberately does not open a private chat on demand.** The actor paths do,
and should: a user may always open a DM with a bot, so a blueprint that never called
`add_private_chat` was only declining to name the chat, not denying it exists. The reverse is
not true. A real bot cannot write into a private chat first — it may only answer a user who
wrote to it — so a test whose bot opens the conversation describes something Telegram would
never allow, and the toolkit has no honest state to invent for it. Opening one here would
make that test pass.

Because the resulting error names a real API branch, the message also names the way to test
that branch: `env.on(SendMessage).raises(TelegramBadRequest, "Bad Request: chat not found")`.
A bot that genuinely handles blocked users keeps its coverage, without the world pretending
to be short of a chat.

The message is built by a helper rather than inline, and a declared user with no private chat
gets a hint of its own naming `add_private_chat`, `ensure_private_chat` and "have the user
write first" — because that is the case this finding actually was, every time.

### D6. Permission couplings are applied on the way in

`restrictChatMember` and `setChatPermissions` do not store the mask they are handed. Both
document, in identical words on the same parameter, that unless
`use_independent_chat_permissions=True` is passed, `can_send_other_messages` and
`can_add_web_page_previews` each imply every message kind, and `can_send_polls` implies
`can_send_messages`. Storing the raw mask produced a member who may send stickers but not
text — a state the real API cannot report — and a bot gating itself on `can_send_messages`
took the branch the fake invented.

`granted_permissions` applies the couplings, then fills the three field-level defaults
(`can_react_to_messages` from `can_send_messages`, `can_edit_tag` and `can_manage_topics`
from `can_pin_messages`). The order matters: a permission a coupling granted is one the
defaults may inherit, which is why `can_send_polls=True` alone comes back with
`can_react_to_messages` true.

Those three are filled **whatever** `use_independent_chat_permissions` says, because the Bot
API documents them on the `ChatPermissions` fields rather than on either method — the switch
speaks only about the couplings the methods themselves list.

Applied on the way *in* rather than on the way out, so `chat.permissions` and
`member.permissions` — which tests read directly — are already what Telegram would report,
and a single place answers for both methods and for every reader.

The result is a `model_copy(update=...)` of the request's own object rather than a fresh
`ChatPermissions`, so whatever a future Bot API version parked in the request's extra fields
survives, and the caller's object is untouched.

### D7. A demotion clears `custom_title`; `tag` survives it

A promotion that grants nothing is a demotion, and it left the member's `custom_title` in
place. Nothing could report it — `ChatMemberMember` has no field for one — so it was invisible
until the next promotion, which resurrected a title nobody had granted.

`tag` is not cleared alongside it, and the asymmetry is the Bot API's own rather than a
judgement call here: `custom_title` is a field of `ChatMemberAdministrator` and
`ChatMemberOwner` only, while `tag` is a field of `ChatMemberMember` and
`ChatMemberRestricted` as much as of the administrator variants. A title describes the
administrator status and goes with it; a tag describes the membership, and a demotion is not
the API's way of taking one away.

### D8. `world.chats` is guarded on assignment, not in `__post_init__`

`ChatRegistry` is what hands each chat its way back to the world, which is what makes
`chat.bound_bot` derivable and every stored message bound. It was installed once in
`__post_init__`, which covered the declared mapping and nothing else. `world.chats = {...}`
after construction — the obvious way to rebuild a world in a fixture — silently swapped it
for a plain `dict`: the chats went in unwired, `bound_bot` was `None` for all of them, and
every message stored afterwards was unbound. That surfaces much later, as a shortcut raising
on a message that looks perfectly ordinary.

Converting in `World.__setattr__` makes the guarantee hold for the *attribute* rather than
for one moment in its life. It subsumes `__post_init__`, which is why that method is gone:
the generated `__init__` assigns `chats` like any other field, so the declared mapping is
converted right there. A value that is already a `ChatRegistry` is assigned through untouched,
so re-assigning the world's own mapping is not a rebuild.

This is the same failure `ChatRegistry` itself was introduced for — `dict.update`,
`setdefault` and `|=` bypassing `__setitem__` — one level up. The pattern is that a
guarantee installed at a moment is a guarantee with doors around it.

### D9. `default_wait_timeout` lives on the world; the environment sets it

Both waits took `timeout=5.0` as a per-call default. A bot whose background work is genuinely
slow repeated `timeout=` on every wait in its suite, and a suite that would rather fail fast
than pause five seconds per timing bug had no way to say so at all for the chat-scoped waits,
which are the ones tests actually write.

The setting is stored on `World` and read by `ChatState.default_wait_timeout` and
`TopicState.default_wait_timeout` as **derived** properties, for the reason `bound_bot` is
derived: one setting, one place holding it, and a chat added after the environment was built
is covered by construction rather than by remembering to copy it. It is `compare=False` on the
dataclass, because it is configuration and not state — two worlds holding the same things
should still compare equal.

The constant behind it is `waiting.DEFAULT_WAIT_TIMEOUT`, so the floor under every wait is one
value rather than a `5.0` repeated at four signatures, and a chat or topic that belongs to no
world still has a timeout.

### D10. `description` becomes the second positional parameter

`description` was keyword-only on `wait_for` and absent from `wait_for_message` entirely. It
is the parameter everybody needs and nobody passes: these waits are written with lambdas, and
for a lambda the description is the *only* thing a timeout message has to say about what was
awaited.

Making it the second positional parameter is the whole fix — `wait_for(lambda: ..., "night to
begin")` costs no ceremony, where `description=` did. It stays accepted as a keyword, so
nothing written against the previous signature breaks, and the two timing parameters stay
keyword-only, where they belong: `timeout` and `interval` are tuning, not description.

`wait_for_message` gains the same parameter in the same position, on both the chat and the
topic form, since a message wait is exactly where a lambda predicate is unavoidable.

## Risks / Trade-offs

- **`chat not found` is no longer a `TelegramBadRequest`** → a test that asserted on that
  will fail. Deliberately: such a test was asserting on the wrong branch. The failure names
  the override that restores the old behavior for tests that really do want the API branch.
- **Permissions read back broader than they were passed** → surprising the first time, and
  correct: it is what the real API reports. `use_independent_chat_permissions=True` stores
  the mask verbatim for tests that want the literal shape, and the couplings are documented
  where a reader meets them.
- **Sorting on insert is O(n) in the worst case** → only for out-of-order registrations,
  which come from one path (a carried message from another environment). The scan runs
  backwards, so the append case, which is everything else, costs one comparison.
- **Evaluating every match instead of stopping at the first** → the same order of work the
  reversed scan already did, and the predicate was already run on every message whenever
  there was no match at all.
- **`World.__setattr__` runs on every attribute write** → one `name == "chats"` comparison,
  on a dataclass whose fields are written a handful of times per test.
- **`owned_or_copied` in `derive_message` widens what an edit may alias** → an edit can now
  put a world-owned object into a stored message by identity, which is exactly what `send`
  already did; the alternative was two triggers disagreeing about one value.

## Migration Plan

Behavioral, and unreleased. The toolkit ships as part of the same unreleased feature, so
there is no released contract to migrate from; the two reversals in D5 and D6 are described
in the changelog fragment and in `docs/dispatcher/testing.rst`, where the bot's own
`except TelegramBadRequest` branch is discussed.

## Open Questions

- Should the outbound path grow an opt-in that *does* open a private chat, for suites whose
  bot legitimately writes first because a previous conversation is assumed? Nothing asked for
  it, and `ensure_private_chat` is one line in a fixture, so the answer for now is no — the
  error names it.
- `granted_permissions` is public in `aiogram.test.modeling` because a handler author needs
  it; it is not exported from `aiogram.test`. If a test needs to compute the couplings itself,
  that is a sign the world should be reporting them somewhere it currently does not.
