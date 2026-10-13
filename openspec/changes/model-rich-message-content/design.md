## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- Sends go through one modeled handler and `build_message`. A payload field such as
  `rich_message` is synthesized, and then `_carry_request_values` overwrites fields of the
  payload with attributes of the *method* that share their name and have a compatible type.
  It never looks inside `method.rich_message`, so the blocks and `is_rtl` are lost and the
  synthesizer's empty `blocks` list wins.
- The synthesizer cannot build most rich blocks on its own. `RichTextUnion` is a
  `TypeAliasType`, which `synthesize` rejects, so a paragraph, heading, caption or details
  block raises `SynthesisError`. `annotation_accepts` also returns `False` for
  `RichTextUnion` against `str`, and for `list[...]` annotations against `list`.
- `handle_edit_text` writes `text`, `entities` and `reply_markup`. An edit carrying only
  `rich_message` therefore clears the text and drops the content.
- `UserActor._iter_buttons` walks `reply_markup.inline_keyboard`. Every button lookup goes
  through it: `click`, the misdirected-click hint, and deep-link button following
  (`_find_deep_link_url` takes the first followable button in iteration order).
  `click(target)` and `follow_deep_link(target)` accept an `InlineKeyboardButton` object
  through an `isinstance` check.
- Copy and forward build the new message with `derive_message`, which keeps every field of
  the original.

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

### D1. Rich content is converted by reflection, field by field

An `InputRich*` model converts to the stored model whose name is the same minus the
`Input` prefix, resolved from `aiogram.types`. The target is built with
`Target.model_validate(values)`, where `values` is assembled per target field:

1. **The same annotation on both sides**: the value is carried as is. This covers rich
   text (`RichTextUnion`, including `RichTextButton`), `buttons:
   list[RichMessageButton]`, table `cells`, `caption: RichBlockCaption`, `location`, and
   every scalar that keeps its type.
2. **An `InputRich*` model, or a list of them, on the input side**: it is converted
   recursively.
3. **An `InputMedia*` on the input side** (`InputMediaPhoto` becoming `list[PhotoSize]`,
   and so on): the target value is synthesized non-empty, exactly as `_nonempty` does for
   `sendPhoto`. Media attributes that the target block carries itself, such as
   `has_spoiler`, are read off the input media.
4. **Required by the target but not set in the input** (a list item's `label`, a map's
   `zoom`, `width` and `height`): the field type's zero value is used (`0`, `""`). It lies
   inside every range the Bot API documents for these fields, and a counter-derived value
   would not (map zoom is 0-24).
5. **`type`**: never carried. The target's own default discriminator is used, since
   `InputRichBlockType` and `RichBlockType` are different enums.

No synthesizer change is needed: only media is synthesized, and media types already
synthesize. The conversion is a module-level function in `modeling.py`, so
`model-ephemeral-messages` can reuse it.

*Alternative considered:* a synthesized base with `_carry_request_values` applied
recursively. Rejected because the review showed it cannot build a paragraph and drops text
and buttons, which are the content this change exists for.

*Alternative considered:* a dict from each `InputRichBlock*` to a converter function. It
would read more explicitly, but 26 block types would need updating on every bump. A new
block type with no entry would be dropped silently, which is the bug being fixed.

### D2. Text edits replace content; the keyboard rule is unchanged

`handle_edit_text` sets either `text`/`entities` or `rich_message`, from whichever the
request carries, and clears the other. Its `reply_markup` handling stays as it is, matching
`editMessageText` in production: the markup the request passes, otherwise none.
`editMessageReplyMarkup` already touches only the markup, so a rich message keeps its
content through it.

### D3. Buttons are found by an ordered walk of the model tree

`_iter_buttons` walks each message's `reply_markup`, then its `rich_message`, depth-first
in document order. It yields every `InlineKeyboardButton` and every `RichMessageButton` it
meets. The walk is iterative, like `mounting.bindables`, but pushes children in reverse so
they pop in document order, and it cannot hit the recursion limit on deep nesting. It does
not know which blocks hold buttons, for the same reason as D1.

Callers read `callback_data` and `url`, which both button types carry. The yielded type is
widened to `InlineKeyboardButton | RichMessageButton`, and `click` and `follow_deep_link`
accept either type as a button object; their `isinstance` checks and docstrings change
accordingly.

*Alternative considered:* a typed walk over `RichBlockButtons` and `RichTextButton`. Rich
text nests through bold, italic, links, list items, details and table cells, so a typed
walk is the hand-kept list again.

## Risks / Trade-offs

- [D1 relies on the `Input` prefix naming convention for rich types] → It holds for every
  `InputRich*` model reachable from `InputRichMessage.blocks`. A guard test walks that
  graph and asserts:
  - each `InputRich*` model has a counterpart;
  - each `InputMedia*` field maps to a target field the synthesizer can fill.

  A bump that breaks either fails loudly instead of dropping content.
  `InputRichMessageContent` (inline results) and `InputRichMessageMedia` have no
  counterpart, and neither is reachable from `blocks`.
- [Zero values for unset required fields (D1, rule 4) are a choice, not Telegram's
  documented defaults] → Telegram does not document what it fills in. Zero values are valid
  and visibly neutral, and the docs say so.
- [Walking model trees (D3) on every click costs more than walking a keyboard] → Messages
  in tests are small, and the walk stops at leaves. Not measurable at test scale.
- [A test that asserted the empty block list now sees blocks] → The old behavior was wrong,
  and the toolkit is in alpha. The changelog fragment states it.

## Migration Plan

None.
