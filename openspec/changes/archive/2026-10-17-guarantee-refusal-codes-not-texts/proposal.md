## Why

Telegram guarantees no error text, only the error code, and the Bot API authors advise clients
to rely on the code. The toolkit's refusals did not follow that: their texts read as Telegram's
own, though some are the Bot API server's, TDLib's or the API docs' and some are the toolkit's
guess, and its tests matched them all. A test that matches a guessed text breaks for no
reason that concerns the bot, and a bot has no way to test its fallback for a text it does not
recognise.

## What Changes

- Every refusal keeps its `error_code` and the exception type for it. The description is a
  heuristic aid and no contract.
- Each refusal's description is declared once, in `aiogram.test.rejections`, marked sourced,
  when it is reproduced verbatim from the Bot API server, TDLib or core.telegram.org as of
  `SOURCES_CHECKED`, or best-effort. `ApiRejection` takes a `retry_after` with a 429 and with
  no other code.
- `rejection_of()` and `rejection_fields()` name the rejection a caught exception came from.
- `BotTestEnvironment(perturb_rejection_descriptions=True)` and the matching fixture reword
  every description, keeping the code and the type, to test a bot's fallback.
- `env.on(...).raises(Error)` without a message words its default under the prefix of the
  type, such as `Forbidden: test error`.
- The requirement on topic rights now says what TDLib does: the rights are checked for a topic
  it holds, and an unknown or deleted topic goes on to the topic's own refusal.
- The toolkit's tests name the rejection instead of matching its description.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains the four requirements below, and states when the
  rights of a topic are checked.

## Impact

- **Code**: `aiogram/test/rejections.py`, `errors.py`, `modeling.py`, `world.py`, `markup.py`,
  `environment.py` and `overrides.py`.
- **Tests**: `tests/test_testing/test_rejections.py`, its `conftest.py`, `test_bot_rights.py`
  and every test that matched a description.
- **Docs**: a new section of `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
