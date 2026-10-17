## Why

The Bot API authors advise clients to rely on the error code rather than on the description.
The toolkit's refusals did not follow that: their texts read as Telegram's own, though some are
the Bot API server's or TDLib's and some are the toolkit's guess, and its tests matched them
all. A test that matches a guessed text breaks for no reason that concerns the bot.

A topic method also skipped the rights check when the topic did not exist, though TDLib checks
`can_manage_topics` or `can_delete_messages` before the topic lookup.

## What Changes

- Every refusal guarantees its `error_code` and the exception type for it. The description is
  best-effort, except for ten texts taken from the Bot API server or TDLib that bots match on,
  which the documentation lists.
- Each refusal's text is declared once, in `aiogram.test.refusals`, marked sourced or
  best-effort. `ApiRejection` takes only a 400, a 403 or a 429, and a 429 only with
  `retry_after`.
- `env.on(...).raises(Error)` without a message words its default under the prefix of the
  type, such as `Forbidden: test error`.
- A topic the bot did not create, or does not exist, takes the right first, so a plain-member
  bot closing an unknown topic is refused for lack of rights.
- The toolkit's tests match a description only for a guaranteed text.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains the two requirements below, and states the rights-first
  order of topic methods for an unknown topic.

## Impact

- **Code**: `aiogram/test/refusals.py`, `errors.py`, `modeling.py`, `world.py`, `markup.py`,
  `environment.py` and `overrides.py`.
- **Tests**: `tests/test_testing/test_refusals.py`, its `conftest.py`, `test_bot_rights.py`
  and every test that matched a description.
- **Docs**: a new section of `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
