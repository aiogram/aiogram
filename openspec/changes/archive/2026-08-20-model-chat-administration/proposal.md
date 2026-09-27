## Why

`GetChat` is modeled, so a test can read a chat back — and it lies. `setChatTitle`,
`setChatDescription`, `setChatPermissions` and `deleteChatPhoto` are all answered with
`True` and discarded, so a handler that renames a group and then reads it back gets the
old title. That is worse than an unmodeled method: the assertion looks meaningful and
silently checks nothing. Telegram also posts a service message into the chat for several
of these (`new_chat_title`, `delete_chat_photo`), which real handlers filter on and which
the fake never produces.

The membership reads have the same shape of gap. `banChatMember`, `unbanChatMember`,
`promoteChatMember` and `restrictChatMember` already mutate `ChatState.members`, but
`getChatAdministrators` and `getChatMemberCount` do not read that state — they synthesize.
So a moderation test can promote a user and then be told by `getChatAdministrators` about
somebody else entirely. Both are one-line derivations over state that already exists.

## What Changes

- **Chat metadata becomes writable state.** `SetChatTitle`, `SetChatDescription`,
  `SetChatPermissions`, `SetChatStickerSet`, `DeleteChatStickerSet` and `DeleteChatPhoto`
  mutate `ChatState`, and the already-modeled `GetChat` reads the new values back.
- **Service messages are emitted where Telegram emits them**: `new_chat_title` on a title
  change and `delete_chat_photo` on a photo removal, appended to the chat like any other
  message so handlers filtering on them can be tested.
- **Membership reads are derived from membership state.** `GetChatAdministrators` filters
  `ChatState.members` by creator/administrator status; `GetChatMemberCount` returns the
  member count.
- **Member annotations are stored.** `SetChatAdministratorCustomTitle` writes the
  `MemberState.custom_title` field that already exists, and `SetChatMemberTag` writes a new
  `MemberState.tag`; `GetChatMember` surfaces both.
- **Errors match Telegram's shape** for the mistakes a test would deliberately provoke:
  an unknown chat or user, a title change on a private chat, permissions on a non-group,
  a custom title for a non-administrator.
- `SetChatPhoto`, `BanChatSenderChat`, `UnbanChatSenderChat`, `VerifyChat` and `VerifyUser`
  stay record-only — media processing and verification badges have nothing a test reads
  back.

No breaking changes. Tests asserting on `env.calls` keep passing; tests asserting on
`get_chat()` start getting truthful answers.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the modeled method set grows to cover chat metadata
  administration and the membership reads, and the requirement that modeled methods return
  state-consistent results is extended to `getChat` and `getChatAdministrators` reflecting
  prior mutations.

## Impact

- **Code**: `aiogram/test/world.py` (`ChatState.description`, `.permissions`, `.photo`,
  `.sticker_set_name`; `MemberState.tag`), `blueprint.py` (declaring those fields),
  `modeling.py` (the handlers and the two service messages, reusing the existing
  `service_message` helper the forum methods already use).
- **Tests**: new cases under `tests/test_testing/`, holding the package at 100%.
- **Docs**: a "Chat administration" section in `docs/dispatcher/testing.rst`.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Compatibility**: no new dependencies; Python 3.10–3.14 and PyPy 3.11 as before.
- **Risk**: moderate and contained. The permission *matrix* is explicitly not enforced —
  the fake stores what was set and never rejects an action for want of a right — so the
  hazard is a reader assuming `setChatPermissions` makes later sends fail. The docs and
  the spec say plainly that it does not.
