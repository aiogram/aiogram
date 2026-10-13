# Tasks

## 1. Presence of restricted users

- [ ] 1.1 Add `MemberState.is_member`, make `is_present` honor it, and report it from `as_chat_member` (design D1); verify with world-level tests and with `getChatMemberCount` not counting a restricted absent user
- [ ] 1.2 Set `is_member` from prior presence in `handle_restrict`, and make actor `join`/`leave` on a restricted user flip `is_member` instead of the status (design D2); verify a restricted absent user, and the leave and rejoin `chat_member` updates carrying restricted on both sides with `is_member` changing and permissions kept

## 2. Lifting and end dates

- [ ] 2.1 Lift a restriction when the granted mask has every permission true, reflecting over `ChatPermissions.model_fields` (design D3); verify lifting a present member gives a plain member, lifting an absent user gives left, and both have no permissions or end date
- [ ] 2.2 Route status changes through one helper that clears `until_date` outside restricted and banned, store no end for a basic-group ban, and report a missing end as the Unix epoch (design D4); verify a permanent ban, unban clearing the end, a basic-group ban, and that `test_ban_accepts_a_timestamp` still passes
- [ ] 2.3 Update the membership section of `docs/dispatcher/testing.rst` for `is_member`, lifting, and the epoch end date; verify the docs build shows no new warnings for `testing.rst`

## 3. Changelog and integration

- [ ] 3.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`; verify the fragment renders in the docs build
- [ ] 3.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, the docs build, and `graphify update .`; verify all pass
- [ ] 3.3 Validate the change with `openspec validate report-restricted-membership-truthfully --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive report-restricted-membership-truthfully`) once its implementation PR into `feature/testing` is merged.
