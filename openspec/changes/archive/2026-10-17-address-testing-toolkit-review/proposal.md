## Why

The review of the toolkit's pull request found ten places where it did not hold to its own
rules, or held to them twice. An anonymous administrator who demoted themself changed the
world and then failed the trigger that did it; a bot could pay, boost and subscribe; a
withheld update could not be answered; a flood limit counted an album once; the bot's cached
`me()` could disagree with `getMe`; and an anonymous vote could land in a poll of another chat.
Four checks ran more often than once.

## What Changes

- An anonymous binding is checked once, as a trigger starts, and never again halfway through,
  so a trigger that ends the actor's own anonymity completes and announces itself.
- Another bot's `pay()`, `pre_checkout_query()`, `shipping_query()`, `purchase_paid_media()`,
  `boost()`, `remove_boost()`, `update_subscription()` and `follow_deep_link()` raise
  `WorldLookupError`, as its `click()` and `vote()` already did.
- An update a trigger withholds is bound to the bot and spares the running tasks, as a fed one.
- A flood limit counts every message of an album or a batch. A call is let through while the
  chat is under a limit, and may take it over.
- `bot.me()` follows a change of `World.bot_group_privacy`.
- A poll records the chat it was sent to, and an anonymous vote in a poll of another chat
  raises `WorldLookupError`.
- A forward or a copy checks the chat and the thread once per call, in one place, and an
  album takes its `media_group_id` once, after the checks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: changes the six requirements below.

## Impact

- **Code**: `aiogram/test/actors.py`, `environment.py`, `flood.py`, `modeling.py`,
  `world.py` and `blueprint.py`.
- **Tests**: `tests/test_testing/test_other_actors.py`, `test_rate_limits.py` and
  `test_message_methods.py`.
- **Docs**: `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
