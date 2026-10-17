## Why

A production bot that runs group games in forum topics end to end on the toolkit could not
reproduce three situations it meets:

- **Other senders.** Only a plain user can act, so a test cannot have another bot post into
  the group, or an anonymous administrator close the game's topic as the group, and check
  what Telegram would deliver and with which sender fields.
- **Topics are the bot's.** A declared topic is announced as the bot's and counts as no
  one's, so a game whose topic a player or the host opened cannot be declared, and neither
  can one the bot opened, whose closed state it posts through.
- **Lost updates.** A trigger always feeds what it produces, so a test cannot change the
  world while the update never arrives, as when infrastructure drops a topic's
  `forum_topic_closed` and the bot learns of the closure only from its next send.

## What Changes

- `Blueprint.add_user(..., is_bot=True, bot_to_bot_mode=...)` declares another bot, and
  `Blueprint(bot_to_bot_mode=..., bot_group_privacy=...)` the bot's own settings. Another bot's
  group message reaches the bot only as Telegram's Bot-to-Bot Communication rules allow;
  otherwise it is stored and the trigger returns the new `Withheld`. Its service messages
  are delivered unless `BotTestEnvironment(deliver_service_messages_from_bots=False)`, or the new
  `bot_env_deliver_service_messages_from_bots` fixture, withholds them.
- `UserActor.in_(chat, anonymous=True)` binds an anonymous administrator, whose messages and
  service messages are from `GroupAnonymousBot`, with the group as `sender_chat` and the
  custom title as `author_signature`.

- `Blueprint.add_topic(..., creator=...)` names who opened a declared topic, a user or the
  bot. Its `forum_topic_created` is from them and the creator's exemptions follow it.
  Without one the topic stays as it was: announced as the bot's, and no one's.

- Every actor trigger that feeds an update takes `deliver=False`, which changes the world and
  stores what the trigger produced as usual, feeds nothing, and returns `Withheld`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains the requirements below.

## Impact

- **Code**: `aiogram/test/actors.py`, `blueprint.py`, `world.py`, `modeling.py`,
  `environment.py`, `plugin.py` and `__init__.py`.
- **Tests**: `tests/test_testing/test_other_actors.py`, `test_topic_creators.py`,
  `test_withheld_updates.py` and `test_plugin.py`.
- **Docs**: two new sections of `docs/dispatcher/testing.rst`, its forum topics section,
  its fixtures and its API reference.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
