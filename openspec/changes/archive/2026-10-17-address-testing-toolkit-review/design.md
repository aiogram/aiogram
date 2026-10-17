## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`.

## Decisions

### D1. An anonymous binding is checked when a trigger starts

Every public trigger of `UserActor` is wrapped by `_trigger`, which asks
`_require_anonymous` once, before the trigger reads or changes anything. Inside a trigger the
chat is read through `_bound_chat`, which does not ask again, and the signature reads the
custom title off the membership the start checked. The public `chat` and `state()` still ask,
for a test that reads them after a demotion. `reply()` is not wrapped, since `send()` is.

### D2. Every person-only trigger refuses a bot

`_refuse_bot` guards the triggers whose update only a person produces: a payment, a query,
a purchased paid media, a boost and its removal, a subscription change and a followed deep
link. The Bot API gives a bot no method for any of them. `manage_bot()` and the others are left
as they were.

### D3. Withholding adopts the update

`BotTestEnvironment.adopt()` is the first half of `feed()`: it spares the running tasks and
binds the update to the bot, or copies it when it belongs to another environment. A withheld
trigger returns the adopted update. It registers no message, since the trigger stored it.

### D4. A flood limit counts messages

No source says how Telegram counts an album. The Bot API FAQ speaks of messages: no more than
one a second in a chat and 20 a minute in a group. Neither the Bot API server nor TDLib
enforces these limits: the server only passes on the 429 and `retry_after` it gets, and TDLib
sends an album as one `messages.sendMultiMedia` request, so the rule lives in Telegram's own
servers and is not public. Counting every message is the cautious reading: a bot that stays
under it stays under any laxer one, and the model never hides a flood.

`admit_send(chat, messages=n)` is called once per call, with the number of messages it puts
into the chat, and records that many stamps once the call succeeds. A call is let through
while the chat is under a limit and may take it over, since a rule for a call that does not
fit is not public either, and an album of ten could never fit one message a second. The next
send then waits for the window to clear. A missing reply in an album is checked before the
limits, as a single send's is, and the album takes its `media_group_id` after them.

### D5. `me()` follows `getMe`

`World.__setattr__` refreshes the bound bot's cached user when `bot_group_privacy` changes,
and `World.bot_me()` is the one place that builds it.

### D6. A poll knows its chat

`PollState.chat_id` is set by `sendPoll`, by a declared poll and by a copy, which is a poll of
the destination. A poll without one, such as one a test stored by hand, is not held against an
anonymous vote. A forward keeps its poll, so a vote in it is still the original chat's.

### D7. The chat and the thread are checked by the handler

`landing()` checks the standing in the chat and the topic, in the order the server does, and
returns where a forward or a copy lands. Each handler calls it once, and `forward_one` and
`copy_one` take the result, so a batch of N no longer runs the checks N times and the order
lives in one place.
