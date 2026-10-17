## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`.

- Every actor trigger builds its update and hands it to `UserActor._feed`, which fed it
  to the dispatcher; the message it carries is stored first.
- A message's sender came from `posted_by(chat, user)`, which made a channel post the
  channel's and anything else the user's.
- `UserSpec` and `UserState` had `is_bot`, which only the bot under test set.
- `TopicState.creator_id` drives every creator exemption: the bot's from `TOPIC_CLOSED`
  (`posting_topic`) and from `can_manage_topics` (`_opened_by_bot`), and a user actor's
  (`_managed_topic`). `Blueprint.build` left it `None` for a declared topic and posted its
  `forum_topic_created` from the bot.

## Decisions

### D1. Another bot is a user with `is_bot`

`add_user(..., is_bot=True)` declares another bot, so it is an actor through `env.user()`
and every rights check a user actor meets applies to it unchanged. `bot_to_bot_mode` is a field
of `UserSpec` and `UserState`, because Telegram's rule reads it on both sides; the bot
under test takes it, and Group Privacy Mode, as `Blueprint(bot_to_bot_mode=...,
bot_group_privacy=...)`, stored on the bot's state and on `World.bot_group_privacy`. A
person with `bot_to_bot_mode` is refused with `ValueError`. `getMe`, and the `Bot`'s cached
`me`, report `can_read_all_group_messages` as the negation of `bot_group_privacy`, as the
Bot API documents that field for `getMe` only.

### D2. One place decides delivery

`_feed` asks `_withheld_by_telegram` before feeding. It looks only at a `message` or
`edited_message` from another bot posting as itself, so channel posts, business
messages, queries and membership updates are fed as before. The rule is the one
core.telegram.org/bots/features states:

- with the mode on for either bot, a `bot_command` entity ending in `@<bot username>`, in
  the text or the caption, or a reply to a message of the bot, gets through;
- with the mode on for the bot, everything gets through while the bot is the owner or an
  administrator, or has privacy mode off.

What is withheld is stored as usual and the trigger returns `Withheld(update, reason)`,
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
caused. The default delivers it; `deliver_service_messages_from_bots=False` withholds it, and
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

### D5. A declared topic names its creator

`TopicSpec.creator_id` is filled from `add_topic(..., creator=...)`, which takes a user as
`members=` does, by spec, actor or id, and `blueprint.bot` for the bot. `build` passes it to
`create_topic` and posts `forum_topic_created` from that user, so the exemptions read one
field and need no change. An undeclared creator fails the build with the world's own
`WorldLookupError`.

The default keeps what a test written earlier relies on: the topic is no one's and its root
is from the bot. The two disagree, and the documentation says so and points at
`creator=blueprint.bot` for a topic the bot is meant to have opened. Making the default the
bot would have exempted the bot from `TOPIC_CLOSED` in every suite that declares a topic,
and turned a test of that refusal green for the wrong reason.

### D6. Withholding is a keyword of every trigger

`deliver` is a keyword-only parameter of each of the forty triggers that feed an update,
next to `**data` (or next to `data=` on `promote` and `demote`), and the internal helpers
pass it down to `_feed`. `_feed` checks it first, so a test's withholding wins over
Telegram's and its reason is the one reported. The world is changed before `_feed` is
reached, as it always was, so nothing about what is stored depends on delivery.

An actor-level switch, such as `alice.withholding().close_topic()`, was considered. A
keyword reads at the call that loses the update, cannot leak into the next trigger, and
matches the one name `Withheld` and `deliver_service_messages_from_bots` use. Its cost is that
`deliver` cannot be dispatcher data, the same as `service_message` on `join()`.

`create_topic()` returns the topic, which the test needs either way, rather than
`Withheld`. `delete_topic()` and `set_topics()` feed nothing, so they take no keyword.

### D7. Who an anonymous binding's other updates name

Only what is posted as the group is from the anonymous bot. A click, an inline query and the
other queries reveal the user, as Telegram shows whoever pressed, so they keep `from_user`
and the user's FSM key, which `env.state(user, chat)` reads; `state()` of the binding reads
the key its messages use. A reaction and a vote name the chat as `actor_chat` and
`voter_chat` with no user, which is what the Bot API's `MessageReactionUpdated` and
`PollAnswer` document for an anonymous user, and are stored under the chat's id. The binding
is rechecked whenever its chat is read and again in `_feed`, so a trigger refuses before it
changes anything once the user lost `is_anonymous`.

### D8. A bot is refused what only a person does

`click()`, `inline_query()`, `chosen_inline_result()` and `vote()` raise for an `is_bot`
actor: the Bot API gives a bot no way to press a button, use inline mode or vote. Delivery no
longer takes a `service` flag from the trigger: a message is a service message when its
`content_type` is none a user can post, so a service message a test builds for another bot
with `send(fields=...)` follows the service switch. A withheld trigger opens an empty route
scope through `trigger()`, so the route readers do not report the trigger before it, and
`Withheld`'s repr names the update id, its kind and the reason rather than the whole update.
