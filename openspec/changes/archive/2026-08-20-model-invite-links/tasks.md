## 1. Invite link state

- [x] 1.1 Add `InviteLinkState` and `ChatState.invite_links` with lookup by URL (design D1)
- [x] 1.2 Add the deterministic URL generator drawn from the world counter (design D2)
- [x] 1.3 Add the shared "revoke current primary, append new primary" transition helper, keeping exactly one active primary
- [x] 1.4 Add conversion from `InviteLinkState` to `ChatInviteLink` at the boundary (design D3)
- [x] 1.5 Tests: registry lookup, URL uniqueness, exactly one active primary after each transition

## 2. Blueprint declaration

- [x] 2.1 Add a frozen invite-link declaration to `Blueprint` (design D6)
- [x] 2.2 Materialize declared links through the same path as created ones
- [x] 2.3 Tests: declared link is editable without being created first; environments stay isolated

## 3. Create and edit

- [x] 3.1 Model `CreateChatInviteLink`
- [x] 3.2 Model `CreateChatSubscriptionInviteLink`, rejecting a `subscription_period` other than the documented constant while accepting a `timedelta` in its place (design D5)
- [x] 3.3 Model `EditChatInviteLink` and `EditChatSubscriptionInviteLink`, mutating and returning the stored link
- [x] 3.4 Raise `TelegramBadRequest` for an unknown link URL and an unknown chat
- [x] 3.5 Tests: create then edit correlates by URL; subscription fields survive an edit; both error paths

## 4. Revoke and export

- [x] 4.1 Model `RevokeChatInviteLink`, returning the stored link marked revoked
- [x] 4.2 Generate a replacement when the revoked link was the primary one (design D4)
- [x] 4.3 Model `ExportChatInviteLink`, revoking the previous primary and returning the new URL
- [x] 4.4 Surface the current primary link on `ChatFullInfo.invite_link` from the modeled `GetChat`
- [x] 4.5 Tests: create then revoke returns the same link; two exports return different URLs with the first revoked; `getChat` reports the current primary; revoking the primary yields a replacement

## 5. Documentation

- [x] 5.1 Add an "Invite links" section to `docs/dispatcher/testing.rst`
- [x] 5.2 State that links are metadata only — no member limits, no expiry, no join-by-link — and that membership is driven by actors
- [x] 5.3 Show correlating by the returned URL rather than by a literal link format
- [x] 5.4 Build docs and fix any new warnings

## 6. Release readiness

- [x] 6.1 `CHANGES/<issue-or-pr>.feature.rst`
- [x] 6.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 6.3 Confirm the parametrized synthesis guard over every generated return type still passes
