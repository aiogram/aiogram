## ADDED Requirements

### Requirement: Another bot can act, and its messages are delivered as Telegram delivers them

A blueprint SHALL declare another bot with `add_user(..., is_bot=True)`, and its
Bot-to-Bot Communication Mode with `bot_to_bot=`, which only a bot SHALL take; the bot under
test SHALL take it as `Blueprint(bot_to_bot=...)`, off by default, and its Group Privacy Mode
as `bot_privacy_mode=`, on by default. Another bot's actor SHALL produce messages and service
messages from it, with `is_bot` set, and SHALL be held to the rights checks of a user actor.
In a group or a supergroup, its message or edit SHALL reach the bot when either bot has the
mode on and the message names the bot in a command or replies to a message of the bot, or
when the bot has the mode on and is an administrator or has privacy mode off. The implicit
reply to a topic's root SHALL NOT count as a reply. Otherwise the message SHALL be stored,
nothing SHALL be fed, and the trigger SHALL return `Undelivered`, carrying the update and
the reason. In a private chat, another bot's message SHALL raise `WorldLookupError` unless
both bots have the mode on. A service message another bot causes SHALL be delivered unless
the environment was built with `deliver_bot_service_messages=False`, or the
`bot_env_deliver_bot_service_messages` fixture returns false, in which case it SHALL be
stored and not fed.

#### Scenario: Another bot's plain message

- **WHEN** another bot posts a plain message in a group and neither bot has the mode on
- **THEN** the message is in the chat, no handler ran, and the trigger returns `Undelivered`

#### Scenario: A command naming the bot

- **WHEN** another bot with the mode on posts `/start@test_bot` in a group
- **THEN** the message is delivered

#### Scenario: An administrator bot reads everything

- **WHEN** the bot has the mode on and is an administrator, and another bot posts a plain
  message
- **THEN** the message is delivered

#### Scenario: A topic another bot closes

- **WHEN** another bot with `can_manage_topics` closes a topic
- **THEN** the topic is closed and `forum_topic_closed`, from that bot, is delivered; with
  `deliver_bot_service_messages=False` it is stored and the trigger returns `Undelivered`

### Requirement: An anonymous administrator posts as the group

`in_(chat, anonymous=True)` SHALL bind an actor that posts as the supergroup: every message
and service message it produces SHALL be from `GroupAnonymousBot` (id 1087968824, first name
`Group`, a bot), with the chat as `sender_chat` and the administrator's custom title, if
any, as `author_signature`. Binding SHALL raise `WorldLookupError` outside a supergroup and
for a user who is not the owner or an administrator with `is_anonymous` set, and so SHALL a
trigger once the user no longer is. The rights checks SHALL be the user's, the bot-to-bot
rule SHALL NOT apply, `state()` SHALL use the FSM key of `GroupAnonymousBot`, a topic it
opens SHALL count as opened by the chat, a membership update it causes SHALL be from
`GroupAnonymousBot`, and joining, leaving or asking to join SHALL raise `WorldLookupError`.

#### Scenario: An anonymous host closes the game's topic

- **WHEN** an administrator with `is_anonymous` and the title "Host" closes a topic
  anonymously
- **THEN** `forum_topic_closed` is from `GroupAnonymousBot`, with the group as
  `sender_chat` and "Host" as `author_signature`, and is delivered

#### Scenario: A plain administrator

- **WHEN** an administrator without `is_anonymous` is bound anonymously
- **THEN** the binding raises `WorldLookupError` naming how to grant it
