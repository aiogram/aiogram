# Tasks

## 1. Rich content is carried

- [ ] 1.1 Add a guard test that walks every model reachable from `InputRichMessage.blocks` and asserts each `InputRich*` model has an `Input`-less counterpart in `aiogram.types` and each `InputMedia*` field maps to a target field the synthesizer can fill (design Risks); verify it passes now and fails when pointed at a model without a counterpart
- [ ] 1.2 Add the module-level `InputRich*` → `Rich*` conversion to `aiogram/test/modeling.py` per design D1 (identical annotations carried, nested input models converted, media synthesized non-empty with `has_spoiler` read off the input media, unset required fields zero-valued, `type` left to the target), and use it for `sendRichMessage` together with `is_rtl`; verify with tests that a paragraph, list, table and button block round-trip, a spoiler photo block stores a non-empty photo marked as a spoiler, an unset map zoom/size and list label get in-range values, and `html`/`markdown`-only input stores an empty block list
- [ ] 1.3 Verify with tests that copying and forwarding a stored rich message keep its rich content
- [ ] 1.4 Document rich content in `docs/dispatcher/testing.rst`: carried blocks, synthesized media, zero values for unset fields, and the `html`/`markdown` and `media` limitations; verify the docs build shows no new warnings for `testing.rst`

## 2. Editing text replaces content

- [ ] 2.1 Make `handle_edit_text` set either text or rich content from the request and clear the other, keeping its `reply_markup` rule (design D2); verify with tests for text → rich, rich → text, the keyboard removed when not passed, and `editMessageReplyMarkup` on a rich message keeping its content

## 3. Buttons inside rich content are clickable

- [ ] 3.1 Rewrite `UserActor._iter_buttons` as an ordered, iterative walk of `reply_markup` then `rich_message` yielding `InlineKeyboardButton | RichMessageButton` (design D3); verify that clicking a callback button in a button block, and in a `RichTextButton` nested in a list item and in a details block, dispatches a `callback_query` with the stored rich message, and that the keyboard button wins over a rich button with the same data
- [ ] 3.2 Widen `click(target)` and `follow_deep_link(target)` to accept a `RichMessageButton` object, with their docstrings; verify with tests that pass a rich button object to each, and that `mypy` passes
- [ ] 3.3 Verify with tests that the misdirected-click hint names another chat holding a rich button, and that a rich `url` button carrying a start link is followed
- [ ] 3.4 Note in `docs/dispatcher/testing.rst` that `click()` and `follow_deep_link()` reach buttons in rich content; verify the example matches a passing test

## 4. Changelog and integration

- [ ] 4.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`, including the observable change that a rich message now carries its blocks; verify the fragment renders in the docs build
- [ ] 4.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, the docs build, and `graphify update .`; verify all pass
- [ ] 4.3 Validate the change with `openspec validate model-rich-message-content --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive model-rich-message-content`) once its implementation PR into `feature/testing` is merged.
