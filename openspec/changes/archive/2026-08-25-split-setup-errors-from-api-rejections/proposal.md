## Why

Everything the fake refused was one exception type. `WorldLookupError` covered both "Telegram
would answer this with a Bad Request" and "your blueprint never declared this", and
`handle_call` converted the lot into `TelegramBadRequest`.

That is right for one half and quietly catastrophic for the other. Real bots wrap their calls:

```python
try:
    await bot.send_message(chat_id=player_id, text="Your role is Mafia")
except TelegramBadRequest:
    await group.answer("Couldn't DM one of you — press Start in my DM first.")
```

Point that bot at a blueprint that forgot to declare a player, and the test passes. It passes
because "User 999999 is not declared in the blueprint" arrived as a `TelegramBadRequest`, the
bot's own `except` swallowed it, and the test exercised the error branch while believing it had
exercised the happy one. The message explaining exactly what to declare was written, converted,
caught and discarded, and the suite stayed green.

The same conversion also mislabelled the things the fake genuinely cannot model. Editing a
message by `inline_message_id` came back as a Bad Request, as if Telegram had refused it — when
the truth is that the toolkit does not model inline messages.

## What Changes

- **Two exception types, with one rule each.** `ApiRejection` is raised for something the real
  Bot API would refuse, carrying Telegram's own wording; `handle_call` turns it into the
  `TelegramBadRequest` a production bot sees. `WorldLookupError` is raised for a gap in the
  test's own setup or a limit of the fake, and **nothing converts it** — it propagates out of
  the call the bot made and fails the test.
- **Every refusal in the package is re-sorted** against that rule. Rejections: an unknown chat
  or message for a call, an administrative action on a private chat, a sticker set name already
  taken, a sticker that is not in a set, a subscription period the API does not permit, a charge
  already refunded, a poll already closed or a message with no poll, a join request that is not
  pending, a query that is not outstanding, a topic that does not exist, an annotation for the
  wrong member status, the chat owner. Setup gaps: an undeclared user, chat, business connection,
  community, sticker set, poll or gift; a charge the environment never recorded; a gift id that
  is not in the fake's catalogue; and `inline_message_id`, which the toolkit does not model.
- **`ApiRejection` is exported** from `aiogram.test`, because reaching into the world directly —
  `chat.require_message(...)`, `chat.topic(...)`, `chat.invite_link(...)` — happens outside any
  call, so there is nothing there to convert the refusal into.
- **The messages earn their keep.** A setup-gap message says what to declare; the gift-catalogue
  one lists the ids the fake actually offers and points at the override for a real one.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the error requirement is split — a modeled rejection behaves like a
  production error, while a setup gap fails the test and is never handed to the bot.

## Impact

- **Code**: `errors.py` gains `ApiRejection`; `world.py`'s `WorldLookupError` gains the
  docstring stating the boundary; `environment.py` converts only `ApiRejection`; every raise
  site in `modeling.py` and `world.py` is re-sorted; `aiogram/test/__init__.py` exports both.
- **Tests**: the suites already asserting on refusals were re-pointed at whichever type the rule
  gives, which is itself the check that the sorting is deliberate.
- **Docs**: a "When a call fails" section in `docs/dispatcher/testing.rst`.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry, which
  states the split.
- **Risk**: the sorting is a judgement per raise site, and a wrong call in the "rejection"
  direction reintroduces exactly the silent-swallow failure. Mitigated by leaving the world's own
  lookups — the largest group of raise sites, and the ones that are setup gaps by construction —
  on the loud type, so only a deliberate edit makes a refusal catchable.
