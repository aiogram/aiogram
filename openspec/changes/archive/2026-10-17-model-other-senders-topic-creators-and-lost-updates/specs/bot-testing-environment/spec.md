## ADDED Requirements

### Requirement: Another bot can be declared and act

A blueprint SHALL declare another bot with `add_user(..., is_bot=True)`. Another bot's actor
SHALL produce messages and service messages from it, with `is_bot` set, and SHALL be held to
the rights checks of a user actor. Its `click()`, `inline_query()`, `chosen_inline_result()`
and `vote()` SHALL raise `WorldLookupError`.

#### Scenario: A bot without the right closes a topic

- **WHEN** another bot that lacks `can_manage_topics` closes a topic
- **THEN** the trigger raises `WorldLookupError` naming the right, and the topic stays open

#### Scenario: A bot presses a button

- **WHEN** another bot's actor clicks a button
- **THEN** the trigger raises `WorldLookupError`, and nothing is fed

### Requirement: The bots' own settings are declared

`add_user(..., bot_to_bot_mode=...)` SHALL declare another bot's Bot-to-Bot Communication
Mode, which only a bot SHALL take, and `Blueprint(bot_to_bot_mode=...)` the bot's own, off by
default. `Blueprint(bot_group_privacy=...)` SHALL declare the bot's Group Privacy, on by
default, and `getMe` SHALL report `can_read_all_group_messages` as its negation.

#### Scenario: A person with the mode

- **WHEN** a blueprint declares a user who is not a bot with `bot_to_bot_mode=True`
- **THEN** the declaration raises `ValueError`

#### Scenario: Group Privacy off

- **WHEN** a blueprint declares `bot_group_privacy=False` and the bot calls `getMe`
- **THEN** `can_read_all_group_messages` is true

### Requirement: Another bot's group message is delivered as Telegram delivers it

In a group or a supergroup, another bot's message or edit SHALL reach the bot when either bot
has the mode on and the message names the bot in a command or replies to a message of the
bot, or when the bot has the mode on and is an administrator or has Group Privacy off. The
implicit reply to a topic's root SHALL NOT count as a reply. Otherwise the message SHALL be
stored, nothing SHALL be fed, and the trigger SHALL return `Withheld`.

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

### Requirement: Another bot writes in private only as Telegram allows

In a private chat, another bot's message SHALL raise `WorldLookupError` unless both bots have
the mode on. In a business chat it SHALL raise unless the sending bot has the mode, and SHALL
then be delivered, which no source states.

#### Scenario: A private message without the mode on both sides

- **WHEN** another bot with the mode on writes to the bot in private, and the bot has it off
- **THEN** the trigger raises `WorldLookupError`, and nothing is stored

#### Scenario: A business chat

- **WHEN** another bot with the mode on writes into a business chat of the bot
- **THEN** the business message is delivered

### Requirement: Other bots' service messages have a switch

A service message another bot causes SHALL be delivered unless the environment was built with
`deliver_service_messages_from_bots=False`, or the `bot_env_deliver_service_messages_from_bots`
fixture returns false, in which case it SHALL be stored and not fed. A message SHALL count as
a service message by what it carries, so one the test builds with `send(fields=...)` SHALL
follow the same switch.

#### Scenario: A topic another bot closes

- **WHEN** another bot with `can_manage_topics` closes a topic
- **THEN** the topic is closed and `forum_topic_closed`, from that bot, is delivered; with
  `deliver_service_messages_from_bots=False` it is stored and the trigger returns `Withheld`

#### Scenario: A service message the test builds

- **WHEN** another bot without the mode sends `fields={"new_chat_title": ...}`
- **THEN** the message is delivered as a service message, not withheld as a plain one

### Requirement: An anonymous administrator posts as the group

`in_(chat, anonymous=True)` SHALL bind an actor that posts as the supergroup: every message
and service message it produces, and every membership update it causes, SHALL be from
`GroupAnonymousBot` (id 1087968824, first name `Group`, a bot), messages with the chat as
`sender_chat`. A message, and never a service message, SHALL carry the administrator's custom
title, if any, as `author_signature`.

#### Scenario: An anonymous host closes the game's topic

- **WHEN** an administrator with `is_anonymous` and the title "Host" closes a topic
  anonymously
- **THEN** `forum_topic_closed` is from `GroupAnonymousBot`, with the group as
  `sender_chat` and no `author_signature`, and is delivered, while a message the host sends
  carries "Host" as `author_signature`

### Requirement: Only an anonymous administrator binds anonymously

Binding anonymously SHALL raise `WorldLookupError` outside a supergroup and for a user who is
not the owner or an administrator with `is_anonymous` set. Every trigger of the binding SHALL
recheck that the user still is, and SHALL raise before changing anything once they are not.
Joining, leaving or asking to join SHALL raise `WorldLookupError` for the binding.

#### Scenario: A plain administrator

- **WHEN** an administrator without `is_anonymous` is bound anonymously
- **THEN** the binding raises `WorldLookupError` naming how to grant it

#### Scenario: Anonymity taken away later

- **WHEN** a bound anonymous administrator loses `is_anonymous` and then promotes a member
- **THEN** the trigger raises `WorldLookupError`, and the member is not promoted

### Requirement: An anonymous administrator keeps the user's rights and topics

The rights checks of an anonymous binding SHALL be the user's, and the bot-to-bot rule SHALL
NOT apply to it. A topic it opens SHALL count as opened by the user, whether bound anonymously
or not, and not by another anonymous administrator.

#### Scenario: A topic opened anonymously

- **WHEN** an administrator without `can_manage_topics` opens a topic anonymously
- **THEN** they close and reopen it, bound anonymously or not, and another anonymous
  administrator without the right cannot

### Requirement: Each update of an anonymous binding names the right sender

`state()` of an anonymous binding SHALL use the FSM key of `GroupAnonymousBot`. A reaction or
a vote it makes SHALL name the chat as `actor_chat` or `voter_chat` and no user, and SHALL be
kept as the chat's. A click, an inline query and the other queries SHALL come from the user,
whose FSM key `env.state(user, chat)` reads.

#### Scenario: An anonymous reaction

- **WHEN** an anonymous administrator reacts to a message
- **THEN** `message_reaction` has the chat as `actor_chat` and no `user`

#### Scenario: An anonymous administrator presses a button

- **WHEN** the binding clicks a button whose handler sets an FSM state
- **THEN** the callback query is from the user, and the state is under the user's key, not
  the binding's

### Requirement: A trigger can change the world and withhold its update

Every actor trigger that feeds an update SHALL take a keyword `deliver`, true by default. With
`deliver=False` the trigger SHALL change the world and store every message it produces, a
service message included, exactly as when it delivers, and SHALL feed nothing to the
dispatcher, every update of a trigger that feeds several included. It SHALL apply to another
bot and to an anonymous administrator alike.

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

### Requirement: A withheld trigger reports itself

A withheld trigger SHALL return `Withheld`, carrying the withheld update and the reason, which
names `deliver=False` when the test withheld it, except `create_topic()`, which SHALL return
the new topic. Whether the test or Telegram withholds it, the trigger SHALL open a route scope
of its own, left empty, so `routes` and `last_route` SHALL NOT report the trigger before it,
and `assert_updates_handled()` SHALL have nothing to flag.

#### Scenario: A withheld trigger after a handled one

- **WHEN** a handled trigger is followed by one with `deliver=False`
- **THEN** `routes` is empty, `last_route` is `None`, and `assert_updates_handled()` passes

#### Scenario: A withheld topic

- **WHEN** a user creates a topic with `deliver=False`
- **THEN** the trigger returns the new topic, and nothing is fed

### Requirement: A declared topic names who opened it

A topic declared with `creator=`, a declared user or the bot, SHALL store that creator, SHALL
have its `forum_topic_created` from them, and SHALL give them the creator's exemptions: the
bot's from `TOPIC_CLOSED` and from `can_manage_topics` for its own topic, and a user actor's
from `can_manage_topics`. A topic declared without one SHALL be no one's, and its
`forum_topic_created` SHALL be from the bot.

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

## MODIFIED Requirements

### Requirement: A declared world matches one built through the API

What a blueprint declares SHALL read back as the same state reached through API calls:
declared permissions SHALL apply the documented defaults, a declared topic SHALL be created
by the path `createForumTopic` takes, and a declared poll SHALL be stored on a message in its
chat.

#### Scenario: Declared permissions follow their defaults

- **WHEN** a blueprint declares a restricted member allowed to send messages
- **THEN** the member reads back allowed to react, as the same restriction through the API
  does

#### Scenario: A declared poll is stored on a message

- **WHEN** a blueprint declares a poll in a chat
- **THEN** the chat holds a message carrying that poll, and users can vote in it
