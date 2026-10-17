## Why

A production bot that runs group games in forum topics vendors the toolkit for
end-to-end tests. It found places where the fake is kinder than Telegram, in ways its
own code can observe:

- **Topic errors are the toolkit's own words.** A call into an unknown thread fails with
  "Topic N does not exist in chat X". Bots match Telegram's texts, so their `except`
  branches never ran.
- **Closed topics are open.** A bot that is a plain member posts into a closed topic, and
  into a closed or hidden General topic. Telegram answers `TOPIC_CLOSED`.
- **Topic messages have no root.** In Telegram a topic message that replies to nothing
  else carries the topic's `forum_topic_created` message as `reply_to_message`. Bots read
  the topic's name from it, and here it was `None`.
- **The bot holds every right.** A bot declared as a plain member pins, deletes others'
  messages, bans, restricts and promotes, and sends what the chat's permissions forbid.
  Telegram refuses each of those, so a bot's "I lack the right" branch went untested.
- **Forum mode only turns on.** `is_forum` becomes true when a topic is declared or
  created and never goes back. A game bot that copes with an owner turning topics off had
  nothing to test against.
- **Users cannot manage topics.** A test that has a user create or close a topic edits the
  world and posts the service message by hand, and can get either wrong.
- **Flood control is untestable.** Nothing in the fake ever answers 429, and declaring
  a `TelegramRetryAfter` takes a constructor call nobody documented.

## What Changes

- Calls into an unknown or deleted topic fail as `message thread not found` and
  `TOPIC_DELETED`; a topic the test names wrongly is a `WorldLookupError`.
- A closed topic refuses the bot's messages with `TOPIC_CLOSED` unless it may manage
  topics.
- A topic message replies to the topic's `forum_topic_created` message unless it replies
  to something else.
- The bot's own calls are checked against its rights, on by default, with
  `enforce_bot_rights=False` to opt out.
- `UserActor.set_topics()` turns a forum off and on, and `add_supergroup(is_forum=True)`
  declares one with no topics.
- User actors create, close, reopen and delete topics and hide, unhide, close and reopen
  the General topic, with the service messages Telegram posts, if they may manage topics.
- A documented `TelegramRetryAfter` override, and opt-in per-chat `RateLimits`.

Observable behavior changes, all toward the Bot API: topic error texts, refusals of the
bot's calls without the right, `reply_to_message` on topic messages, and
`createForumTopic` in a supergroup that is not a forum. The toolkit is in alpha.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains seven requirements and loses "Permissions are stored
  but not enforced", which the bot's rights check replaces.

## Impact

- **Code**: `aiogram/test/world.py`, `modeling.py`, `actors.py`, `blueprint.py`,
  `environment.py`, `errors.py`, `plugin.py`, and the new `flood.py`.
- **Tests**: `tests/test_testing/` gains `test_forum_rules.py`, `test_bot_rights.py`,
  `test_rate_limits.py` and `test_user_topic_actions.py`. 84 existing tests now declare the bot's standing.
- **Docs**: the forum topics, chat administration and overrides sections of
  `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
