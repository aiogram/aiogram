## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- Sends go through one modeled handler and `build_message`. A payload field such as
  `rich_message` is synthesized, and then `_carry_request_values` overwrites it with the
  request's values. That overwrite runs one level deep and only where the annotations
  agree. `InputRichMessage.blocks` (`list[InputRichBlockUnion]`) never agrees with
  `RichMessage.blocks` (`list[RichBlockUnion]`), so nothing is carried and the
  synthesizer's empty list wins.
- `handle_edit_text` writes `text`, `entities` and `reply_markup`, so an edit that only
  carries `rich_message` clears the text and drops the content.
- `UserActor._iter_buttons` walks `reply_markup.inline_keyboard`. Every button lookup goes
  through it: `click`, the misdirected-click hint, and deep-link button following.

## Goals / Non-Goals

**Goals:**

- No hand-kept list of rich block types anywhere in the toolkit. The next Bot API bump that
  adds a block type or a container should need no toolkit change, as with updates and
  administrator rights today.

**Non-Goals:**

- Parsing `html` or `markdown` rich input into blocks. That is Telegram's renderer, and a
  partial copy would produce content Telegram would not.
- Resolving `InputRichMessage.media`, media that rich text references through
  `tg://photo?id=`-style links. Those links stay in the text as given.

## Decisions

### D1. Rich content is converted by reflection, not by a block table

An `InputRich*` model converts to the stored model whose name is the same minus the
`Input` prefix, resolved from `aiogram.types`. Fields are matched by name:

- a value whose type the target annotation accepts is carried;
- a nested `InputRich*` model, or a list of them, is converted recursively;
- anything else is left to the synthesizer. That covers media (`InputMediaPhoto` becomes
  `list[PhotoSize]`) and the target's required fields the input lacks (`label`, a map's
  dimensions).

The target starts as a synthesized instance and the converted fields are applied over it,
so every required field always has a value. This is `_carry_request_values` applied
recursively, and it reuses the same `annotation_accepts`.

Rich text (`RichTextUnion`, including `RichTextButton`) is shared between input and
output, so it is carried as-is.

The conversion is a public helper of the modeling layer. `model-ephemeral-messages` uses
it for `editEphemeralMessageText(rich_message=...)`.

*Alternative considered:* a dict from each `InputRichBlock*` to a converter function. It
would read more explicitly, but 26 block types would need updating on every bump. A new
block type with no entry would be dropped silently, which is the bug being fixed.

### D2. Buttons are found by walking the model tree

`_iter_buttons` yields every `InlineKeyboardButton` and every `RichMessageButton` it finds
by walking the message's `reply_markup` and `rich_message` as pydantic model trees. It
does not know which blocks hold buttons, for the same reason as D1. Callers only read
`callback_data` and `url`, which both button types carry, so `click`, the hint and
deep-link following gain rich buttons with no change of their own.

*Alternative considered:* a typed walk over `RichBlockButtons` and `RichTextButton`. Rich
text nests through bold, italic, links, list items, details and table cells, so a typed
walk is the hand-kept list again.

## Risks / Trade-offs

- [D1 relies on the `Input` prefix naming convention] → It holds for every model
  reachable from `InputRichMessage.blocks` in the current schema. A guard test walks that
  graph and asserts that each model has a counterpart, so a bump that breaks the
  convention fails loudly instead of dropping content. `InputRichMessageContent` (inline
  results) and `InputRichMessageMedia` have no counterpart, and neither is reachable from
  `blocks`.
- [Walking model trees (D2) on every click costs more than walking a keyboard] → Messages
  in tests are small, and the walk stops at leaves. Not measurable at test scale.
- [A test that asserted the empty block list now sees blocks] → The old behavior was wrong,
  and the toolkit has not been released. The changelog fragment states it.

## Migration Plan

None.
