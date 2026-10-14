## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. Each finding came from a reproduced audit of the
fake API. This document records only the choices the fixes make; the rest follows the Bot
API text directly.

## Goals / Non-Goals

**Goals:**

- Follow only rules the Bot API states, citing the text.
- Prefer reflection over hand-kept lists, so a Bot API bump needs no toolkit change.

**Non-Goals:**

- Error wording: tests assert the exception type.
- Cross-chat replies as `external_reply`: a reply to another chat's message is resolved
  and validated, but `external_reply` is not synthesized.
- A sticker's media type matching its `InputSticker.format`: stickers stay synthesized.

## Decisions

### D1. Enumerated strings come from `aiogram.enums` by name

A synthesized `str` field named `f` on a model `M` takes the first member of the enum
`aiogram.enums.<M><F>` when one exists (`Sticker.type` from `StickerType`, `Chat.type`
from `ChatType`, `Dice.emoji` from `DiceEmoji`). This reflects the convention butcher
generates enums by, so the set follows the Bot API. Fields with no such enum keep today's
value.

### D2. Booleans are false; counts of nothing are zero

A synthesized `bool` is `False`, the absent-flag reading every optional Bot API boolean
documents. A synthesized `int` whose name ends in `_count` is `0`, because synthesized lists
are empty and a count that disagrees with its list breaks the obvious `[0]` access.

### D3. File ids come from a world counter

`World` numbers synthesized files (`file-<n>`, `unique-<n>`). Uploads register their bytes
under that id. A `str` media input, which is a file id the bot passed, becomes the stored
`file_id`.

### D4. Dice values fold into the emoji's range

The synthesized value is reduced into 1..6 for 🎲 🎯 🎳, 1..5 for 🏀 ⚽ and 1..64 for 🎰,
which is the table the Bot API gives.

### D5. Copy exclusions read the message's own fields

A message is a service message when it carries none of the content fields a send method
produces. The toolkit tests that against `MEDIA_FIELDS`, text, rich content and poll, so no
list of service fields is kept. Invoice, paid media, giveaway and giveaway-winners messages
are named, as the Bot API names them.

### D6. Star transactions keep their partner

`StarTransactionState` stores the partner user id. `as_star_transaction` reports
`id=charge_id or id`, `amount=abs(amount)`, and a `TransactionPartnerUser` as `source` for
income and as `receiver` for an outgoing payment.

### D7. Declared state goes through the API's own paths

`Blueprint.build` runs declared permissions through `granted_permissions` (moved into
`world.py` to avoid an import cycle), creates declared topics with the bot as `from_user`,
and stores a declared poll the way `sendPoll` does, on a message from the bot.

## Risks / Trade-offs

- [Tests that pinned the old behavior change] → each such test asserted a divergence from
  the Bot API; the toolkit is in alpha.
- [Booleans synthesized as false change synthesized results everywhere] → optional flags
  read as absent, which is what most Bot API booleans default to; required booleans that
  should be true in context are seeded by their handlers already (`is_bot` on the bot).
