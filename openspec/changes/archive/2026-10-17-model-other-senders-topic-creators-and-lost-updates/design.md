## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`.

- Every actor trigger builds its update and hands it to `UserActor._feed`, which fed it
  to the dispatcher; the message it carries is stored first.
- A message's sender came from `posted_by(chat, user)`, which made a channel post the
  channel's and anything else the user's.
- `UserSpec` and `UserState` had `is_bot`, which only the bot under test set.

## Decisions

### D1. Another bot is a user with `is_bot`

`add_user(..., is_bot=True)` declares another bot, so it is an actor through `env.user()`
and every rights check a user actor meets applies to it unchanged. `bot_to_bot` is a field
of `UserSpec` and `UserState`, because Telegram's rule reads it on both sides; the bot
under test takes it, and Group Privacy Mode, as `Blueprint(bot_to_bot=...,
bot_privacy_mode=...)`, stored on the bot's state and on `World.bot_privacy_mode`. A
person with `bot_to_bot` is refused with `ValueError`. `getMe` is left as it was.

### D2. One place decides delivery

`_feed` asks `_withheld_by_telegram` before feeding. It looks only at a `message` or
`edited_message` from another bot posting as itself, so channel posts, business
messages, queries and membership updates are fed as before. The rule is the one
core.telegram.org/bots/features states:

- with the mode on for either bot, a `bot_command` entity ending in `@<bot username>`, in
  the text or the caption, or a reply to a message of the bot, gets through;
- with the mode on for the bot, everything gets through while the bot is the owner or an
  administrator, or has privacy mode off.

What is withheld is stored as usual and the trigger returns `Undelivered(update, reason)`,
a frozen dataclass, instead of the handler's result. Nothing is routed, so
`assert_updates_handled()` sees nothing to flag. In a private chat the features page
requires the mode on both sides for a bot to message another at all, so `_build_message`
raises `WorldLookupError` before anything is stored.

**Assumptions.** The implicit reply to a topic's root does not count as a reply to the bot
that opened the topic, since Telegram speaks of replying directly. Edits follow the rule for
messages.

### D3. Service messages of other bots have a switch

The Bot API server does not filter updates by sender (`need_skip_update_message` in
Client.cpp skips outgoing, old, self-destructing and imported messages, and a few
content types), and the features page lists "All service messages" among what every bot
receives. Neither says what Telegram's servers send for a service message another bot
caused. The default delivers it; `deliver_bot_service_messages=False` withholds it, and
`_feed` is told which messages are service messages by the triggers that build them.

### D4. An anonymous administrator is a binding

`in_(chat, anonymous=True)` keeps the user and changes only who the messages are from,
so rights stay the user's. `posted_by` recognises the anonymous bot and gives the chat as
`sender_chat`, which is the Bot API server's mapping run backwards (Client.cpp,
`create_message`: a sender chat equal to the chat becomes `group_anonymous_bot_user_id`).
The user is TDLib's (UserManager.cpp, `get_anonymous_bot_user_id` and `get_user_force`):
id 1087968824, first name `Group`, username `GroupAnonymousBot`, a bot, built fresh per
message since a message binds what it carries. `author_signature` is the custom title, as
the Bot API's `Message.author_signature` documents; the service-message helpers of
`modeling.py` take it as `signature`.

The binding requires a supergroup, as `Message.sender_chat` names "the supergroup itself",
and an owner or administrator whose `is_anonymous` is set, which `getChatMember` reports.
It is checked when binding and again on each message. `state()` uses the anonymous bot's id,
the key the dispatcher derives from `from_user`.

**Assumptions.** A `chat_member` update an anonymous administrator causes is from the
anonymous bot; TDLib passes the actor through as the server sends it, and no source read
says what that is. The signature on a service message is likewise unconfirmed. A topic
opened anonymously counts as the chat's, after TDLib's creator being a chat or a user.
Joining and leaving refuse an anonymous binding.
