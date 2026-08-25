## Why

Invite-link management is a self-contained cluster of six methods that is useless one
method at a time and genuinely valuable as a whole. Today every one of them is
synthesized, which means `revokeChatInviteLink` returns a *different* link than the one
`createChatInviteLink` returned moments earlier, `editChatInviteLink` reports a name and
member limit unrelated to what was passed, and `exportChatInviteLink` returns a fresh
string that `getChat` never mentions. A bot that creates a link, stores its URL, and later
revokes it — the standard paid-access pattern — cannot be tested at all: the id it stored
and the id it revokes have nothing to do with each other.

The state required is small and belongs to a chat: a list of links, each with its creator,
name, limits, expiry and revoked flag. Every method in the cluster reads or writes exactly
that list, and `getChat` gains a truthful `invite_link`.

## What Changes

- **`InviteLinkState` on `ChatState`.** Each link carries its URL, creator, name, expiry,
  member limit, join-request flag, subscription period and price where applicable, and a
  revoked flag.
- **The cluster is modeled**: `CreateChatInviteLink`,
  `CreateChatSubscriptionInviteLink`, `EditChatInviteLink`,
  `EditChatSubscriptionInviteLink`, `RevokeChatInviteLink` and `ExportChatInviteLink`.
  Editing and revoking return **the stored link**, mutated — not a new object.
- **`exportChatInviteLink` replaces the primary link**, as Telegram does: each call revokes
  the previous primary link and returns a new one, and `getChat` reports the current
  primary link.
- **Blueprint declaration** of existing links, so a test can start from a chat that already
  has one rather than creating it first.
- **Errors match Telegram's shape** for the mistakes a test would provoke: editing or
  revoking a link the chat does not have, and a subscription period other than the one
  value the Bot API permits.

No breaking changes. Tests asserting on `env.calls` keep passing; tests correlating a
created link with a later edit or revoke start working.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the modeled method set grows to cover invite-link management,
  and the chat's primary invite link becomes state that `getChat` reports.

## Impact

- **Code**: `aiogram/test/world.py` (`InviteLinkState`, `ChatState.invite_links`,
  `ChatState.primary_invite_link`), `blueprint.py` (declaring links), `modeling.py`
  (six handlers plus the `getChat` field).
- **Tests**: a new module under `tests/test_testing/`, holding the package at 100%.
- **Docs**: an "Invite links" section in `docs/dispatcher/testing.rst`.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Compatibility**: no new dependencies; Python 3.10–3.14 and PyPy 3.11 as before.
- **Risk**: low. The cluster is closed — no other part of the world reads invite links —
  and the link-joining side (a user actually joining *via* a link, incrementing a counter)
  is explicitly out of scope, so there is no half-modeled edge.
