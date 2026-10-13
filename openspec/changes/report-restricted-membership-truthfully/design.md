## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- `MemberState` has one `status`. Presence is derived from it (`is_present` is "not left,
  not kicked"), so `RESTRICTED` always reads as present.
- `as_chat_member` builds `ChatMemberRestricted(is_member=True, until_date=self.until_date
  or BASE_DATE)` and `ChatMemberBanned(until_date=self.until_date or BASE_DATE)`. The
  member branch passes `until_date` through as a subscription expiry.
- `handle_restrict` always sets `RESTRICTED`. `handle_ban` sets `KICKED`. `handle_unban`
  sets `LEFT`. None of them touch `until_date` except to set it.
- `UserActor._change_membership(status, ...)` overwrites `status` for `join`/`leave` and
  reads the old and new `ChatMember` around the change.
- `getChatMemberCount` counts `is_present` members.

## Goals / Non-Goals

**Goals:**

- One place decides presence, and every reader (`as_chat_member`, member count,
  administrator list, actors) goes through it.

**Non-Goals:**

- Expiry of `until_date` over time. That needs a clock and is specified by
  `add-controllable-world-time`, which builds on this change.
- Enforcing permissions. The existing requirement "Permissions are stored but not enforced"
  stands.

## Decisions

### D1. Presence is stored for restricted users only

`MemberState` gains `is_member: bool = True`, meaningful only while `status` is
`RESTRICTED`. `is_present` becomes: not left, not kicked, and not restricted-and-absent.
`as_chat_member` reports the stored `is_member`. Other statuses already encode presence in
their status, so they need no flag. Blueprint-declared restricted members keep today's
default of present.

*Alternative considered:* a general `is_present` field for every status. Two sources of
truth for "left" would disagree sooner or later. The flag is confined to the one status
whose Bot API variant carries it.

### D2. Restrict keeps presence; join and leave keep restrictions

- `handle_restrict` sets `is_member` from the user's presence before the call.
- `_change_membership` on a restricted user flips `is_member` instead of overwriting
  `status`. Its old/new read-around then produces the restricted → restricted update with
  `is_member` changing, as Telegram does.

### D3. Lifting is detected on the granted mask

After `granted_permissions` applies the Bot API couplings, a mask with every
`ChatPermissions` field true lifts the restriction. The check reflects over
`model_fields`, so a permission a later Bot API adds is included automatically. A lifted
user becomes `MEMBER` if present and `LEFT` otherwise, and their permissions and
`until_date` are cleared.

### D4. `until_date` is normalized on every transition

- One helper sets a member's status, and clears `until_date` unless the new status is
  `RESTRICTED` or `KICKED`. Every handler and actor path goes through it.
- A ban in a chat of type `group` stores no end.
- `as_chat_member` reports a missing end as `datetime(1970, 1, 1, tzinfo=UTC)`. That is
  what aiogram parses `0` into, and what a bot reading the field sees.

### D5. `only_if_banned` is read

`handle_unban` returns without a change when `only_if_banned` is set and the user is not
banned. Otherwise it moves the user to `LEFT` through the status helper, which also covers
the documented default of removing a present member.

## Risks / Trade-offs

- [The restricted → restricted update on leave is inferred from `is_member`'s existence and
  wording ("a member of the chat at the moment of the request")] → It is the only shape
  that keeps the restriction the Bot API says survives. The docs say so.
- [Tests that counted a restricted absent user, or asserted `BASE_DATE` for a permanent
  ban, change expectation] → Both asserted behavior that disagreed with the Bot API. Stated
  in the changelog.

## Migration Plan

None at runtime.
