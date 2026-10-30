## Why

An audit of the fake Bot API found about two dozen places where a modeled method, a
synthesized result or a declared world disagrees with what the Bot API documents, in ways a
bot under test can observe. Each one was reproduced. For example:

- `sendMediaGroup` returns messages with no media and no caption.
- `unpinChatMessage` without an id unpins everything instead of the newest pin.
- Every synthesized file has the same `file_id`, so a second upload overwrites the first
  one's downloadable content.
- `sendDice` returns `emoji='emoji'` and values above 6.
- Copying ignores `message_thread_id`, `caption_entities` and `reply_markup`, and copies
  service messages the Bot API says cannot be copied.
- A quiz loses its `correct_option_ids`.
- Star transactions report refunds and payments with the wrong id, sign and partner.

The toolkit is in alpha, and each of these makes a test pass or fail for a reason
production would not share.

## What Changes

- **Messages:**
  - Media groups store each item's media and caption under one `media_group_id`, and
    refuse fewer than 2 or more than 10 items.
  - Replies resolve their target in the chat `reply_parameters.chat_id` names. A missing
    target fails unless `allow_sending_without_reply` is set.
  - Copies and forwards follow the documented rules: target thread, new caption and
    entities, `reply_markup`, and no copying of service, invoice, paid-media or giveaway
    messages, nor forwarding of protected content.
  - Unpinning without an id unpins the newest pin.
  - Editing text or caption is refused on a message that has none of that content.
- **Polls:**
  - Quizzes keep `correct_option_ids`, regular polls allow revoting by default, a quiz
    without a correct answer is refused, and `stopPoll` stores its `reply_markup`.
- **Topics and business:**
  - Hiding the General topic closes it and reopening it unhides it. `editForumTopic` with
    an empty name keeps the current one.
  - `deleteBusinessMessages` deletes in one chat only.
- **Content and synthesis:**
  - Checklists store the content they were sent or edited with.
  - Files get unique ids, and a file id a request passes is the id stored.
  - Dice carry their emoji and a value in its range.
  - Synthesized string fields whose values aiogram enumerates take a valid value,
    synthesized booleans are false, and counts of empty lists are zero.
  - Every rich media block converts, voice notes included.
- **Stars and administrators:**
  - Star transactions report Telegram's id, a positive amount and the partner.
  - An administrator the bot promoted reports `can_be_edited`.
- **Declared worlds match API-built ones:**
  - Declared permissions apply the documented defaults.
  - Declared topics are created by the bot.
  - A blueprint can declare a poll, as the spec already requires.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains requirements for each group above. No existing
  requirement text changes; the declared-poll requirement already exists and is now
  implemented.

## Impact

- **Code**: `aiogram/test/modeling.py`, `aiogram/test/world.py`,
  `aiogram/test/synthesis.py`, `aiogram/test/blueprint.py` and `aiogram/test/rich.py`. No
  generated code changes.
- **Tests**: `tests/test_testing/` gains a regression test per finding, and tests that
  pinned the old behavior change.
- **Docs**: `docs/dispatcher/testing.rst` where it describes the affected methods.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: after the four Bot API 10.3 changes; independent of
  `align-actor-triggers-with-bot-api`, except that both touch polls (this change stores
  the rules, that one enforces them on votes).
