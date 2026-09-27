## Why

`follow_deep_link` grew its link-kind table one field-feedback round at a time —
`2026-08-25-follow-deep-links` shipped `start` plus the handful of kinds that showed up in the
group-bot scenario the toolkit was built against (`startgroup`, `startapp`, `startchannel`,
`startattach`, `attach`, invite links, extra path segments), and
`2026-08-25-apply-wave-2-field-feedback` added the precedence rule for `?start=x&startapp=y`.
Nothing had checked the table against Telegram's own link reference. Auditing `_LINK_KINDS`
against https://core.telegram.org/api/links found real gaps, not just missing rows:

- **`t.me/$<slug>` (an invoice link) parsed as a `start` link to a bogus username.** The old
  path-classifier only recognized `+<hash>` and `joinchat/<hash>`; anything else with one path
  segment fell through to "the segment is the username", so `t.me/$AbCdEfGhIj` classified as a
  `start` link to `@$AbCdEfGhIj` — a username Telegram would never issue, compared against the
  bot's real one, and rejected for the wrong reason (a bot-mismatch, not an invoice link).
- **`t.me/+<digits>` (a phone-number link) was indistinguishable from `t.me/+<hash>` (an
  invite link).** Both parsed as `kind="invite"`, so a test with a phone link on a button was
  told it "offers to join a private chat" — a claim about a chat that link never names.
- **A `tg://` url whose host was not `resolve` returned `None`** — "not a Telegram deep-link
  url" — even for `tg://join?invite=...`, `tg://boost?...` and every other host Telegram
  documents. Those are real Telegram links; refusing to recognize them as links at all was a
  stronger claim than the toolkit meant to make.
- **Every unfollowable kind was refused with the same generic wording** (`_unresolvable_rejection`,
  `_unfollowable_start_rejection`), naming the general shape of the problem rather than the
  action the test could actually take. Telegram documents roughly two dozen link formats;
  `_LINK_KINDS` covered nine.
- **A `start` payload was replayed unchecked.** Bot API deep linking allows only `A-Z`, `a-z`,
  `0-9`, `_` and `-`, 1-64 characters; a button built with a payload outside that alphabet would
  never make a real client send `/start`, but the toolkit sent it anyway, letting a test pass on
  a bug in the button the bot itself built.

## What Changes

- **Classify every link format https://core.telegram.org/api/links documents**, one
  `_LinkKindPolicy` row per kind, replacing the nine-row table with one covering both the
  bot-addressing kinds (`start`, `startgroup`, `startapp`, `startchannel`, `startattach`,
  `attach`, `miniapp`, `game`, `referral`, `profile`, `draft`, `unknown_query`) and the kinds
  that address something else (`phone`, `invite`, `joinchat`, `message_link`, `story`, `share`,
  `invoice`, `boost`, `videochat`, `business`, `stickerset`, `entity_ref`, `service_path`,
  `extra_path`). `_bot_link` and `_foreign_link` build the two families' rejection wording
  consistently instead of each row hand-writing its own string.
- **`_path_deep_link` classifies every documented path shape**: an invite hash or phone number
  behind `+`, an invoice behind `$` or `/invoice/`, a reserved segment (`_RESERVED_PATH_KINDS`
  — `/share`, `/addstickers`, `/boost`, `/m`, `/c`, and the service paths this toolkit does not
  tell apart), a story under `/s/`, a message by numeric id, and a direct Mini App by its short
  name — the one path form that does address a bot.
- **`tg://` hosts other than `resolve` are classified by host** (`_TG_HOST_KINDS`), down to a
  `service_path` fallback for any host Telegram adds that this table does not enumerate by
  name — never reported as not a Telegram link.
- **A phone-number link is told apart from an invite link** by its all-digit tail, the same way
  Telegram's own clients tell them apart, on both the `t.me/+` and `tg://resolve?phone=` forms.
- **Two rejections point at the trigger that models the action**: an invoice link says to use
  `pay()` or `pre_checkout_query()`, a boost link says to use `boost()`, instead of only naming
  what the link opens.
- **A `start` payload is validated** against `[A-Za-z0-9_-]{1,64}` before being followed, in both
  the explicit-target and automatic-scan paths; an invalid one raises naming the rule.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the `follow_deep_link` refusal requirement is amended to describe
  spec-grounded classification of every documented link format and `start` payload validation,
  in place of the smaller hand-picked set it previously described.

## Impact

- **Code**: `aiogram/test/actors.py` — `_LINK_KINDS`, `_bot_link`, `_foreign_link`,
  `_path_deep_link`, `_QUERY_KIND_ALIASES`, `_QUERY_KIND_LOOKUP`, `_RESERVED_PATH_KINDS`,
  `_TG_HOST_KINDS`, `_require_valid_start_payload`, `_parse_deep_link`.
- **Tests**: `tests/test_testing/test_deep_links.py` gains `TestLinkFormatsFromTheSpec`,
  `TestPhoneLinksAreNotInviteLinks`, `TestTgSchemeVariants`, `TestStartPayloadValidation` and
  `TestStartGroupAdminCompanion`.
- **Docs**: the "Deep links" section of `docs/dispatcher/testing.rst` names every refused
  format instead of five, and states the payload-validation rule.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry.
- **Risk**: none of this changes what a test can make the toolkit *do* — `start` was already
  the only followable kind, and every previously-refused link is still refused. The change is
  entirely in what the refusal says and which additional formats it now recognizes by name
  instead of by accident (a bogus start) or by omission ("not a Telegram link").
