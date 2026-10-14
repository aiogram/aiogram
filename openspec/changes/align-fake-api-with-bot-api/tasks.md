# Tasks

## 1. Messages

- [x] 1.1 Store each media group item's media, caption and entities under one `media_group_id`, refusing fewer than 2 or more than 10 items; verify with an album test and a one-item refusal
- [x] 1.2 Resolve reply targets in `reply_parameters.chat_id` or the target chat, set `reply_to_message` only within the same chat and `external_reply` otherwise, and refuse a missing target unless `allow_sending_without_reply`; verify the three scenarios
- [x] 1.3 Make copy and forward honour `message_thread_id` (cleared outside forums), copy's `caption`/`caption_entities`/`reply_markup`, and the documented exclusions with batch skipping (design D5); verify each scenario
- [x] 1.4 Unpin only the newest pin (by date, then id) when no id is given; verify the two-pin scenario
- [x] 1.5 Refuse `editMessageText` without text or rich content and `editMessageCaption` without captionable media, for the regular and ephemeral edits; verify both refusals

## 2. Polls, topics, business, checklists

- [x] 2.1 Store `correct_option_ids` (falling back to the deprecated single id), default `allows_revoting` to true outside quizzes, refuse a quiz without correct ids, and store `stopPoll`'s `reply_markup`; verify each scenario
- [x] 2.2 Couple hiding/reopening the General topic, and keep the name on an empty `editForumTopic` name and drop the icon on an empty emoji id; verify each
- [x] 2.3 Confine `deleteBusinessMessages` to one chat and refuse mixed chats, numbering business messages per connection (design D8); verify both scenarios
- [x] 2.4 Convert `InputChecklist` into the stored `Checklist` for send and edit; verify title and tasks round-trip

## 3. Synthesis and content

- [x] 3.1 Synthesize enumerated strings from `aiogram.enums` by name, booleans as false and counts of lists as zero (design D1, D2); verify a sticker, a chat and the profile photos result
- [x] 3.2 Number files from a world counter and store a passed file id (design D3); verify two uploads download their own bytes and a resent id is kept
- [x] 3.3 Fold dice values into the emoji's range with 🎲 as default (design D4); verify values for each emoji
- [x] 3.4 Convert every rich media block, including ones whose input media does not subclass `InputMedia`; verify a voice-note block

## 4. Stars, administrators, declared worlds

- [x] 4.1 Report star transactions with the charge id, positive amounts and partners (design D6); verify a payment and its refund
- [x] 4.2 Record who promoted an administrator and report `can_be_edited`; verify a bot promotion and a declared administrator
- [x] 4.3 Build declared permissions through `granted_permissions`, declared topics with the bot as creator, and add `Blueprint.add_poll` (design D7); verify each scenario
- [x] 4.4 Correct the `ChatRegistry` error message's copy recipe to one that works in a running environment; verify the message

## 5. Docs, changelog and integration

- [x] 5.1 Update `docs/dispatcher/testing.rst` for each changed method and `Blueprint.add_poll`; verify the docs build shows no new warnings
- [x] 5.2 Fold the user-visible changes into `CHANGES/1887.feature.rst`
- [x] 5.3 Run `make lint` and `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage; verify both pass
- [x] 5.4 Validate with `openspec validate align-fake-api-with-bot-api --strict`
