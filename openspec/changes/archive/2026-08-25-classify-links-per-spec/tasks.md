## 1. Audit against the spec

- [x] 1.1 Walk https://core.telegram.org/api/links kind by kind against `_LINK_KINDS`, listing
      every documented format the table did not yet name
- [x] 1.2 Confirm `t.me/$<slug>` parsed as a `start` link to a bogus username (invoice-slug bug)
- [x] 1.3 Confirm `t.me/+<digits>` parsed identically to `t.me/+<hash>` (phone-vs-invite bug)
- [x] 1.4 Confirm a `tg://` host other than `resolve` returned `None` — "not a Telegram
      deep-link url" — for every host, including ones the spec documents (design D4)

## 2. The policy table

- [x] 2.1 Add `_bot_link(reason, *, instead, query_key=True)` and `_foreign_link(reason, *,
      instead="", query_key=False)`, replacing the three bespoke `_..._rejection` helpers
      (design D1)
- [x] 2.2 Add `addresses_username` and `query_key` to `_LinkKindPolicy`, so `follow_deep_link`
      and `_parse_deep_link` read structural facts off the table instead of re-deriving them
- [x] 2.3 Add one row per bot-addressing kind: `start`, `startgroup`, `startchannel`,
      `startapp`, `miniapp`, `startattach`, `attach`, `game`, `referral`, `profile`, `draft`,
      `unknown_query`
- [x] 2.4 Add one row per kind addressing something else: `phone`, `invite`, `joinchat`,
      `message_link`, `story`, `share`, `invoice`, `boost`, `videochat`, `business`,
      `stickerset`, `entity_ref`, `service_path`, `extra_path`
- [x] 2.5 Point the `invoice` and `boost` rejections at `pay()` / `pre_checkout_query()` and
      `boost()` respectively (design D5)

## 3. Parsing every documented shape

- [x] 3.1 Add `_path_deep_link`, classifying `+digits` (phone), `+hash` (invite), `$slug` and
      `/invoice/slug` (invoice), `_RESERVED_PATH_KINDS` segments, `/s/...` (story), an
      all-digit tail (message link, including the threaded form), and a single short-name
      segment (the direct Mini App form that does address a bot) (design D2, D3)
- [x] 3.2 Add `_QUERY_KIND_ALIASES` (`appname`, `text`, `ref`, `livestream`, `voicechat`,
      `post`) so a query spelled differently from its kind's name still reaches the same row
- [x] 3.3 Add `_QUERY_KIND_LOOKUP`, checking `start` first so it wins over a co-occurring
      start-ish parameter regardless of table order
- [x] 3.4 Add `_TG_HOST_KINDS`, classifying `tg://` hosts other than `resolve`, falling back to
      `service_path` for any host it does not enumerate (design D4)
- [x] 3.5 Add `_require_valid_start_payload`, checking the payload against
      `[A-Za-z0-9_-]{1,64}` and raising naming the rule when it fails (design D6)
- [x] 3.6 Call it from `follow_deep_link` after the kind and username are already confirmed to
      be a matching `start` link (design D6)

## 4. Tests

- [x] 4.1 `TestLinkFormatsFromTheSpec`: one parametrized case per newly-classified format —
      direct Mini App, message (plain, threaded, private-channel), story, share (all its
      forms), invoice (all its forms), boost (all its forms), video-chat (including legacy
      spellings), business chat, sticker/emoji sets, game, draft, referral, profile, and
      service links (proxy, language pack, login code, chat folder)
- [x] 4.2 `TestPhoneLinksAreNotInviteLinks`: a phone link is refused as a phone link and the
      message does not say "invite"; an invite hash is refused as an invite and the message
      does not say "phone"
- [x] 4.3 `TestTgSchemeVariants`: `tg://join` classifies like its `t.me` twin; `tg://user`
      names the Bot API entity-reference abstraction; an unenumerated host is a service link
- [x] 4.4 `TestStartPayloadValidation`: valid payloads at the boundary (64 characters, dash and
      underscore, base64url-shaped) are followed; an over-long, percent-encoded or non-Latin
      payload is refused naming the rule, whether reached by an explicit target or by the
      automatic scan
- [x] 4.5 `TestStartGroupAdminCompanion`: a `startgroup` / `startchannel` link carrying the
      `admin=` companion parameter is still refused as the chooser link it is

## 5. Documentation

- [x] 5.1 Rewrite the "Deep links" refusal paragraph in `docs/dispatcher/testing.rst` to name
      every documented format, the `pay()` / `boost()` pointers, the phone-vs-invite
      distinction, and `?text=` draft semantics, with one example refusal message
- [x] 5.2 State the payload-validation rule in the same section
- [x] 5.3 Amend the "Only start links are followed..." requirement in
      `openspec/specs/bot-testing-environment/spec.md` to the spec-grounded classification and
      payload validation
- [x] 5.4 Adjust the deep-link sentence in `CHANGES/1887.feature.rst` to match

## 6. Release readiness

- [x] 6.1 No new changelog fragment: folded into the toolkit's existing
      `CHANGES/1887.feature.rst` entry
- [x] 6.2 `uv run pytest tests/test_testing -q` unchanged at 1242 passed, 1 skipped
- [x] 6.3 docutils parse of `docs/dispatcher/testing.rst` and `CHANGES/1887.feature.rst`: no
      structural errors (sphinx-role warnings expected and ignored)
