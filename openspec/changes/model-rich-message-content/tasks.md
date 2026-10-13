# Tasks

## 1. Rich content is carried

- [ ] 1.1 Add a recursive `InputRich*` → `RichBlock*` conversion to `aiogram/test/modeling.py` per design D1 (synthesized base, carry by name where the annotation accepts, recurse into nested input models and lists, synthesize the rest), and use it for `sendRichMessage`; verify with tests that a sent paragraph/list/button block/table round-trips into the stored message, a photo block carries a schema-valid synthesized photo, a list item gets a synthesized `label`, and `html`/`markdown`-only input stores an empty block list
- [ ] 1.2 Add a guard test that walks every model reachable from `InputRichMessage.blocks` and asserts each has an `Input`-less counterpart in `aiogram.types`; verify it passes now and fails when pointed at a model without one
- [ ] 1.3 Make `editMessageText(rich_message=...)` replace the stored rich content through the same conversion without clearing other fields; verify with a test that edits a rich message and asserts the new blocks and an untouched `reply_markup`
- [ ] 1.4 Document rich content in `docs/dispatcher/testing.rst` (carried blocks, synthesized media, the `html`/`markdown` and `media` limitations); verify the docs build shows no new warnings for `testing.rst`

## 2. Buttons inside rich content are clickable

- [ ] 2.1 Rewrite `UserActor._iter_buttons` to walk `reply_markup` and `rich_message` as model trees and yield both `InlineKeyboardButton` and `RichMessageButton` (design D2); verify that clicking a callback button in a button block, and in a `RichTextButton` nested in a list item and in a details block, dispatches a `callback_query` with the stored rich message
- [ ] 2.2 Verify the misdirected-click hint and deep-link button following work on rich buttons, with tests for a rich button in another chat and for a rich `url` button carrying a start link
- [ ] 2.3 Note in `docs/dispatcher/testing.rst` that `click()` reaches buttons in rich content; verify the example in the docs matches a passing test

## 3. Changelog and integration

- [ ] 3.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`, including the observable change that a rich message now carries its blocks; verify the fragment renders in the docs build
- [ ] 3.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, and the docs build; verify all pass
- [ ] 3.3 Validate the change with `openspec validate model-rich-message-content --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive model-rich-message-content`) once its implementation PR into `feature/testing` is merged.
