## 1. Chat state growth

- [x] 1.1 Add `description`, `permissions`, `photo` and `sticker_set_name` to `ChatState` (design D1)
- [x] 1.2 Make each declarable on the blueprint and deep-copied by `Blueprint.build()`
- [x] 1.3 Extend `handle_get_chat` to surface all four on `ChatFullInfo`
- [x] 1.4 Tests: declared values reach `getChat`; environments stay isolated

## 2. Metadata mutations

- [x] 2.1 Model `SetChatTitle` and `SetChatDescription`
- [x] 2.2 Model `SetChatPermissions`
- [x] 2.3 Model `SetChatStickerSet` and `DeleteChatStickerSet` (no-op when unset, design open question)
- [x] 2.4 Model `DeleteChatPhoto` as a transition to `None`; leave `SetChatPhoto` record-only
- [x] 2.5 Raise `TelegramBadRequest` for an unknown chat and for administrative actions on a private chat (design D4)
- [x] 2.6 Tests per method: `getChat` reports the new value, other chats unaffected, both error paths

## 3. Service messages

- [x] 3.1 Emit `new_chat_title` from `SetChatTitle` through the existing `service_message` helper (design D2)
- [x] 3.2 Emit `delete_chat_photo` from `DeleteChatPhoto`
- [x] 3.3 Tests: the service message is appended to the chat with a real `message_id` and reaches a handler filtering on it

## 4. Membership reads

- [x] 4.1 Model `GetChatMemberCount` as a derivation over the *present* members of `ChatState.members` (design D3)
- [x] 4.2 Model `GetChatAdministrators` filtering by creator/administrator status, creator first, omitting other bots unless `return_bots` (design D6)
- [x] 4.3 Raise `TelegramBadRequest` for an unknown chat
- [x] 4.4 Tests: promote then read the administrator list; ban then read the count; creator ordering; unknown chat fails

## 5. Member annotations

- [x] 5.1 Model `SetChatAdministratorCustomTitle` writing the existing `MemberState.custom_title` (design D5)
- [x] 5.2 Add `MemberState.tag` and model `SetChatMemberTag`
- [x] 5.3 Raise `TelegramBadRequest` for an unknown user, for a custom title on a non-administrator, and for a tag on a non-regular member (design D5)
- [x] 5.4 Tests: both round-trip through `getChatMember`; both error paths

## 6. Documentation

- [x] 6.1 Add a "Chat administration" section to `docs/dispatcher/testing.rst`
- [x] 6.2 State plainly that permissions and administrator rights are stored but never enforced, and show the override recipe for testing a rejection
- [x] 6.3 Note that a rename appends a service message, so message counts include it
- [x] 6.4 Build docs and fix any new warnings

## 7. Release readiness

- [x] 7.1 `CHANGES/<issue-or-pr>.feature.rst`, calling out that `getChat` now reflects prior mutations and that renames emit a service message
- [x] 7.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 7.3 Confirm the parametrized synthesis guard over every generated return type still passes
