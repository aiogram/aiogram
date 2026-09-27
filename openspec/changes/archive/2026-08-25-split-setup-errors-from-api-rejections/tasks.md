## 1. The two types

- [x] 1.1 Add `ApiRejection` to `aiogram/test/errors.py`, documenting that its message is
      Telegram's own wording without the `Bad Request:` prefix (design D1, D2)
- [x] 1.2 Rewrite `WorldLookupError`'s docstring to state that it is a setup gap and that nothing
      converts it
- [x] 1.3 Export both from `aiogram.test` (design D3)
- [x] 1.4 Convert only `ApiRejection` in `BotTestEnvironment.handle_call`, letting
      `WorldLookupError` propagate

## 2. Re-sorting every refusal

- [x] 2.1 Rejections in `modeling.py`: chat not found, message to edit/forward/copy/delete/pin/
      react to/read not found, no personal chat, an administrative action on a private chat, a
      sticker set name already taken, a subscription period the API does not permit, a link that
      is not a subscription link, a charge already refunded, `sendGift` with neither recipient,
      a poll already closed or a message with no poll, a join request that is not pending, an
      annotation for the wrong member status (design D1)
- [x] 2.2 Rejections in `world.py`: a message the chat does not hold, a topic that does not
      exist, an invite link the chat does not have, a sticker that is not in a set, a query that
      is not outstanding (design D5)
- [x] 2.3 Setup gaps stay on `WorldLookupError`: an undeclared user, chat, business connection,
      community, sticker set or poll; a sticker in no set at all; a gift nobody owns; a charge
      never recorded; a chat id with no chat to add; the General topic asked for as a
      `ForumTopic`
- [x] 2.4 `inline_message_id` keeps `WorldLookupError` — the toolkit does not model inline
      messages, and saying Telegram refused would be untrue
- [x] 2.5 Improve the gift-catalogue message to list the ids the fake offers and point at the
      override for a real one

## 3. Where the rule lives

- [x] 3.1 State both rules in `modeling.py`'s module docstring, beside the copy boundary, where a
      handler author reads them (design D4)
- [x] 3.2 Cross-reference the two exception docstrings, so either entry point explains the other

## 4. Tests

- [x] 4.1 Re-point every existing refusal assertion at the type the rule gives, asserting the
      type explicitly rather than a base class
- [x] 4.2 Cover both halves through a real call: a modeled rejection reaches the caller as a
      `TelegramBadRequest` carrying Telegram's wording (`test_errors.py`), while a call naming
      something the blueprint never declared raises `WorldLookupError` out of `await
      env.bot....` unconverted (`test_sticker_sets.py`, `test_stars_and_gifts.py`,
      `test_chat_administration.py`)
- [x] 4.3 Cover the direct-world path: `chat.topic(999)` and `chat.require_message(999)` raise
      `ApiRejection` outside any call

## 5. Documentation

- [x] 5.1 Add a "When a call fails" section to `docs/dispatcher/testing.rst`
- [x] 5.2 Show both, and state why the distinction exists — a Bad Request would be swallowed by
      the bot's own error handling and the test would pass while testing nothing
- [x] 5.3 Note that the things the fake genuinely cannot model raise loudly too, with
      `inline_message_id` as the example
- [x] 5.4 Note that reaching into the world directly surfaces `ApiRejection` unconverted
- [x] 5.5 Add both exceptions to the API reference; build docs and fix any new warnings

## 6. Release readiness

- [x] 6.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry,
      which states the split in its own paragraph
- [x] 6.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview
      aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q
      --cov=aiogram --cov-report=term-missing` at 100%
