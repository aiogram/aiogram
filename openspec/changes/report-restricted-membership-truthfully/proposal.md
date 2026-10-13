## Why

The toolkit's model of a restricted or banned member disagrees with the Bot API in ways a
bot can observe. A review of the time proposal found them, and they stand on their own:

- **Every restricted user reads as present.** `as_chat_member` always reports
  `is_member=True`. Restricting someone who is not in the chat, which the Bot API allows,
  makes them count in `getChatMemberCount`.
- **Leaving loses the restriction.** A restricted member who leaves becomes `left`. Telegram
  keeps the restriction and reports `is_member=False`.
- **A restriction cannot be lifted by granting everything.** `restrictChatMember` with every
  permission granted should lift it ("Pass True for all permissions to lift restrictions
  from a user"). The toolkit keeps the member restricted.
- **"Forever" reads as a date.** A mute or ban with no end is reported with the fixed
  `BASE_DATE`, which reads as a date in the past. The Bot API uses `0` (the Unix epoch).
- **Stale `until_date`.** It survives a status change. A plain member then reports an old
  restriction date in `ChatMemberMember.until_date`, which means subscription expiry.
- **Basic groups.** A ban's `until_date` in a basic group is stored, though the Bot API
  applies it "for supergroups and channels only".

## What Changes

- A restricted user's presence is stored separately from the restriction and reported
  through `is_member`. Only present users count as members.
- Leaving and rejoining keep a restriction, moving only `is_member`, in the membership
  update as well as in reads.
- `restrictChatMember` granting every permission lifts the restriction: the user is a
  member if present, otherwise left, with no `until_date`.
- A restriction or ban with no end reports `until_date` as the Unix epoch.
- Any change to a status other than restricted or banned clears `until_date`.
- A ban in a basic group is stored with no end, whatever `until_date` says.

Observable behavior changes, all toward the Bot API:

- the member count;
- `is_member`;
- the membership updates of a restricted member leaving or joining;
- the "forever" `until_date`.

The toolkit is in alpha.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains three requirements, covering presence of restricted
  users, lifting a restriction, and how `until_date` is reported. No existing requirement
  text changes. "Membership reads are derived from membership state" keeps holding, and
  its member-count scenario now counts present users only.

## Impact

- **Code**:
  - `aiogram/test/world.py`: `MemberState` presence, `is_present`, `as_chat_member`.
  - `aiogram/test/modeling.py`: the restrict, ban, unban and promote handlers.
  - `aiogram/test/actors.py`: join and leave of a restricted member.
- **Tests**: `tests/test_testing/` gains cases for each point. `test_modeling.py`'s
  `test_ban_accepts_a_timestamp` (an `until_date` of `0`) keeps passing, now as "forever".
- **Docs**: the membership section of `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: independent of the rich and ephemeral changes. `add-controllable-world-time`
  builds on it.
