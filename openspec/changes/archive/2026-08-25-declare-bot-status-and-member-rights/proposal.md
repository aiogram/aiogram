## Why

A group bot's first move is almost always checking its own standing:

```python
me = await bot.get_chat_member(chat_id=message.chat.id, user_id=bot.id)
if not me.can_delete_messages:
    await message.answer("Give me the right to delete messages first.")
```

The toolkit could not test either branch. The bot was appended to every declared group as a
plain `MEMBER` with no way to say otherwise, so the "I am an admin" path was unreachable; and
`ChatMemberAdministrator` was fabricated at conversion time with a fixed, flattering mask, so
the "I am missing a right" path was unreachable too. The rights a test declared went nowhere,
because there was nowhere to put them.

`promoteChatMember` had the same hole from the other side. It stored a *status* and threw the
rights away, so a bot that promoted a moderator with `can_pin_messages=True` and later read
the member back was told they could delete messages, restrict members and change the chat
info as well. Worse, the demotion rule keyed off "no `can_*` field is true" computed over the
whole method, so `promote_chat_member(is_anonymous=True)` — hiding an admin, not demoting one
— silently stripped the administrator.

Two more gaps came out of the same review. The fake was *more permissive* than the API it
stands in for: `banChatMember`, `restrictChatMember` and `promoteChatMember` all happily acted
on the chat's owner, which Telegram refuses with "can't remove chat owner". A bot moderating a
list of users would therefore pass its tests and fail in production. And the rights conversion
reported every field in every chat, while the real API reports `can_post_messages` only in
channels and `can_manage_topics` only in supergroups — so a bot reading
`member.can_post_messages` in a supergroup got a fabricated `True` where Telegram sends
nothing.

## What Changes

- **The bot's own status in a group-like chat is declarable.** `add_group`, `add_supergroup`
  and `add_channel` accept `bot_status`, and `blueprint.bot` may appear in `members` directly.
  They are two ways of saying the same thing, so passing both raises rather than letting one
  silently shadow the other.
- **Rights and permissions become membership state.** `MemberState` carries `rights` and
  `permissions`; `getChatMember` and `getChatAdministrators` report what was actually granted
  rather than a default.
- **`Blueprint.set_member` declares what a member may *do*.** It amends a member declared by
  the `members=` shorthand or adds a new one; passing `rights` or `permissions` implies the
  status that carries it, and declaring both for one member raises, since they belong to
  different statuses.
- **`administrator_rights(**overrides)` is exported** as the one place the ordinary
  administrator mask is built, so "an admin who cannot delete messages" is one line.
- **`promoteChatMember` persists exactly what it granted.** The whole mask is stored on every
  call, an omitted right is not granted, and a promotion in which nothing comes out true is the
  demotion the Bot API documents — with `is_anonymous` counting as a right like any other.
  `restrictChatMember` likewise stores the permissions it was given and clears any rights.
- **Rights are reported per chat type.** A right the Bot API does not report in a chat reads
  back as `None` there, however it was declared, and a right it does report reads back as a
  plain boolean even when it was left unstated.
- **The chat owner is protected.** Promoting, demoting, banning or restricting the creator
  fails with Telegram's own "can't remove chat owner".

Permissions and rights are still **stored, never enforced** — that non-goal is unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the membership model gains rights and permissions as declared and
  written state, chat-type-scoped reporting, and the owner guard; the existing
  administration requirements are extended rather than duplicated.

## Impact

- **Code**: `world.py` (`MemberState.rights` / `.permissions`, `CHAT_TYPE_SCOPED_RIGHTS`,
  `mask`, `scoped_rights`, `administrator_rights`, `no_administrator_rights`, and
  `as_chat_member` taking the chat type); `blueprint.py` (`bot_status`, `MemberSpec.rights` /
  `.permissions`, `set_member`); `modeling.py` (`handle_promote`, `handle_restrict`, the
  `_not_the_owner` guard, and passing the chat type into every membership read).
- **Tests**: new suites in `tests/test_testing/test_chat_administration.py` covering
  declaration, persistence, chat-type scoping and the owner guard.
- **Docs**: the "Chat administration" section gains the declaration recipes and the scoping
  rule.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry.
- **Risk**: `getChatMember` answers change shape for administrators — fields that used to be
  `True` everywhere are now `None` outside the chat types that report them. That is the point,
  but it is a behavior change for anything that asserted on the old answer.
