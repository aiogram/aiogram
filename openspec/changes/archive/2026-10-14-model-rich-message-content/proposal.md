## Why

`sendRichMessage` stores a message whose `rich_message` is a synthesized empty
`RichMessage(blocks=[])`: the blocks the bot sent are dropped. This predates Bot API 10.3,
but 10.3 put callback buttons inside rich blocks (`RichBlockButtons`, `RichTextButton`).
A bot that sends one that way now gets `WorldLookupError: No message ... carries a button`
when a test clicks it. That breaks the spec's existing promise that a button on a rich
message is clickable. `editMessageText(rich_message=...)` drops the new content too, and
also clears the stored text.

## What Changes

- **Rich content is carried, not synthesized.** A sent, copied or forwarded rich message
  stores the blocks and settings its request stated. They are converted from the
  `InputRichBlock*` shapes to the `RichBlock*` shapes Telegram returns. Media inside blocks
  is synthesized as it is for `sendPhoto` and its siblings. A required field the input
  leaves unset gets a valid zero value. `html` and `markdown` input is not parsed into
  blocks; that limitation is documented.
- **`editMessageText` replaces either kind of content.** Rich content replaces text and
  text replaces rich content. The keyboard rule is unchanged.
- **`click()` and `follow_deep_link()` reach buttons inside rich content** at any nesting
  depth, as well as in `reply_markup`, and accept a rich button object. The
  misdirected-click hint covers them too.

No API breaks. Observable behavior changes in one place: a rich message now carries its
blocks instead of an empty list.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains three requirements. They are "A rich message carries the
  content its request stated", "Editing text replaces either kind of content" and "Buttons
  inside rich content are clickable". No existing requirement text changes.

## Impact

- **Code**: `aiogram/test/rich.py` (new: the conversion), `aiogram/test/modeling.py` (the
  send and edit-text handlers), `aiogram/test/synthesis.py` (the shared `nonempty`), and
  `aiogram/test/actors.py` (button search, and the `click` and `follow_deep_link`
  signatures). No generated code changes.
- **Tests**: `tests/test_testing/` covers the conversion, a guard on the `Input` naming
  convention, rich edits, and clicks inside rich content.
- **Docs**: a rich content section in `docs/dispatcher/testing.rst`, including the
  `html`/`markdown` limitation.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: lands first. `model-ephemeral-messages` reuses its conversion for
  `editEphemeralMessageText(rich_message=...)`.
