## ADDED Requirements

### Requirement: Another bot can act, and its messages are delivered as Telegram delivers them

A blueprint SHALL declare another bot with `add_user(..., is_bot=True)`, and its
Bot-to-Bot Communication Mode with `bot_to_bot_mode=`, which only a bot SHALL take; the bot under
test SHALL take it as `Blueprint(bot_to_bot_mode=...)`, off by default, and its Group Privacy Mode
as `bot_group_privacy=`, on by default, which `getMe` SHALL report as
`can_read_all_group_messages` being its negation. Another bot's actor SHALL produce messages and service
messages from it, with `is_bot` set, and SHALL be held to the rights checks of a user actor.
In a group or a supergroup, its message or edit SHALL reach the bot when either bot has the
mode on and the message names the bot in a command or replies to a message of the bot, or
when the bot has the mode on and is an administrator or has privacy mode off. The implicit
reply to a topic's root SHALL NOT count as a reply. Otherwise the message SHALL be stored,
nothing SHALL be fed, and the trigger SHALL return `Withheld`, carrying the update and
the reason. In a private chat, another bot's message SHALL raise `WorldLookupError` unless
both bots have the mode on. A service message another bot causes SHALL be delivered unless
the environment was built with `deliver_service_messages_from_bots=False`, or the
`bot_env_deliver_service_messages_from_bots` fixture returns false, in which case it SHALL be
stored and not fed.

#### Scenario: Another bot's plain message

- **WHEN** another bot posts a plain message in a group and neither bot has the mode on
- **THEN** the message is in the chat, no handler ran, and the trigger returns `Withheld`

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
  `deliver_service_messages_from_bots=False` it is stored and the trigger returns `Withheld`

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

### Requirement: A trigger can change the world and withhold its update

Every actor trigger that feeds an update SHALL take a keyword `deliver`, true by default. With
`deliver=False` the trigger SHALL change the world and store every message it produces, a
service message included, exactly as when it delivers, and SHALL feed nothing to the
dispatcher, every update of a trigger that feeds several included. It SHALL return
`Withheld`, carrying the withheld update and a reason naming `deliver=False`, except
`create_topic()`, which SHALL return the new topic. Nothing SHALL be routed, so
`assert_updates_handled()` SHALL have nothing to flag. It SHALL apply to another bot and to an
anonymous administrator alike.

#### Scenario: A lost closure

- **WHEN** an administrator closes a topic with `deliver=False`
- **THEN** the topic is closed and `forum_topic_closed` is stored, no handler ran, and the
  trigger returns `Withheld` carrying that message

#### Scenario: The bot learns from its next send

- **WHEN** the closure was withheld and a player sends a command in the topic, and the bot
  answers into it
- **THEN** the bot's send fails with `TOPIC_CLOSED`

#### Scenario: A join withholds both updates

- **WHEN** a user joins with `deliver=False`
- **THEN** the user is a member, `new_chat_members` is stored, and neither update is fed

## MODIFIED Requirements

### Requirement: A declared world matches one built through the API

What a blueprint declares SHALL read back as the same state reached through API calls:
declared permissions SHALL apply the documented defaults, a declared topic SHALL be created
by the path `createForumTopic` takes, and a declared poll SHALL be stored on a message in its
chat. A topic declared with `creator=`, a declared user or the bot, SHALL store that creator,
SHALL have its `forum_topic_created` from them, and SHALL give them the creator's exemptions:
the bot's from `TOPIC_CLOSED` and from `can_manage_topics` for its own topic, and a user
actor's from `can_manage_topics`. A topic declared without one SHALL be no one's, and its
`forum_topic_created` SHALL be from the bot.

#### Scenario: Declared permissions follow their defaults

- **WHEN** a blueprint declares a restricted member allowed to send messages
- **THEN** the member reads back allowed to react, as the same restriction through the API
  does

#### Scenario: A declared poll is stored on a message

- **WHEN** a blueprint declares a poll in a chat
- **THEN** the chat holds a message carrying that poll, and users can vote in it

#### Scenario: A topic the bot opened

- **WHEN** a blueprint declares a topic with `creator=blueprint.bot` and the topic is closed
- **THEN** the bot, a plain member, posts into it and closes and reopens it

#### Scenario: A topic a player opened

- **WHEN** a blueprint declares a topic with a user as its creator
- **THEN** its `forum_topic_created` is from that user, who closes it without
  `can_manage_topics`, and the bot's send into it while it is closed fails with
  `TOPIC_CLOSED`

#### Scenario: A topic declared without a creator

- **WHEN** a blueprint declares a topic without `creator=`
- **THEN** its `forum_topic_created` is from the bot, and neither the bot nor a user gets
  a creator's exemption
