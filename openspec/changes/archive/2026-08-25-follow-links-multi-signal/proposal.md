## Why

Wave-3's field report against the same production bot converged on one systemic diagnosis
behind five otherwise-unrelated `follow_deep_link` bugs: the classifier's data model gave
each link kind exactly one row and one signal — a username, a boolean "does this address a
bot", a fixed position in a lookup table — while several of Telegram's own documented links
carry *more than one signal at once*, and the toolkit kept reading only the one the table had
room for.

- `attach` addresses a *chat* in its username slot and names the bot in its `attach`
  parameter instead. `_LinkKindPolicy.addresses_username` had room for only one boolean, so
  the toolkit read the username slot for every bot-concerning kind alike — the scan skipped
  every `attach` button of this bot's as another chat's, and an explicit follow refused it as
  "not to this bot" before the kind's own attachment-menu message could ever fire. The same
  gap hid a second signal on the `t.me/+<phone>?attach=<bot>` and `tg://resolve?phone=…&attach=…`
  forms, which need the phone number *not* read as a phone-number link once `attach` is beside
  it.
- `?start=&startapp=y` carries two signals — an empty `start` and a real `startapp` — and the
  classifier's "start wins whenever present" rule only checked presence, not value, so an
  empty `start` claimed the link and buried the Mini App a tapping user actually gets.
- `?startapp=x&text=y` and `?appname=shop&startapp=ref` each carry a real format's parameter
  next to a parameter that is *also* that format's own companion signal (`startapp` is both a
  format and the start parameter of a named Mini App; `text` is both a format and a draft
  alongside `?profile`). A single lookup-table order could not honor both directions at once:
  aliases-first read the first pair as an unsent draft instead of the Mini App it is, while
  plain table order read the second as the bot's *main* app rather than the *named* one
  `appname` selects.
- `t.me/s/<username>` was never itself in the two-row `path` / `query` split
  `_path_deep_link` used to classify `t.me` urls — it fell through to the direct-Mini-App
  path shape and came back naming a bot called `s` and an app named after the channel,
  neither of which exists.
- The default payload alphabet check is a single signal (does the payload match `A-Z a-z 0-9
  _ -`), but production bots receive `start` payloads that break it — base64 padding, dots,
  over-long strings — because the Bot API states the rule without any client enforcing it. A
  test reproducing that traffic had no way to ask the toolkit to replay it as delivered rather
  than refuse it as a bug.

## What Changes

- **`_LinkKindPolicy.match_by` replaces `addresses_username: bool`.** The field is now a slot
  name (`"username"`, `"payload"`, or empty), so a kind can name which parsed slot carries the
  bot it concerns instead of always being read off the username. `attach` is the one kind that
  sets `match_by="payload"`; every other bot-concerning kind keeps `"username"`. A single
  `_addressed_bot(deep_link)` lookup replaces the two separate `addresses_username` checks in
  `follow_deep_link` and the automatic scan, so the two can no longer disagree about whether a
  button is this bot's.
- **The phone-plus-`attach` co-occurrence is read as the attachment-menu link, not the phone
  link**, on both the `t.me/+<phone>?attach=<bot>` and `tg://resolve?phone=…&attach=…` forms:
  `_path_deep_link` takes the query and defers to it when `attach` is present, and the
  `tg://resolve` phone branch does the same.
- **`start` only takes its precedence with a non-empty value.** `?start=&startapp=y`
  classifies as the `startapp` link it also is; a bare `?start=` with nothing else in the
  query is still the plain start it already was.
- **`_QUERY_KIND_LOOKUP` sorts companions last** rather than fixing one static order: every
  key that is also a documented companion of another format (`startapp`, `startattach`,
  `text`, tracked in `_COMPANION_QUERY_KEYS`) is checked only after every key that is not, so
  `?startapp=x&text=y` reads as the Mini App link and `?appname=shop&startapp=ref` reads as
  the *named* Mini App — both directions the two static orderings could not hold at once. A
  companion parameter appearing alone in the query still classifies by the format it names.
- **`channel_preview` is a kind of its own.** `t.me/s/<username>` is reserved in
  `_RESERVED_PATH_KINDS` ahead of the direct-Mini-App path shape, since `s` is a single-letter
  segment Telegram's own username rules already exclude from being a real bot.
- **`follow_deep_link(validate_payload=False)`** drops the deep-linking alphabet check and
  replays the payload exactly as the button carries it, for tests reproducing what a real
  client actually delivered. The default stays `True`; the flag changes only that one check —
  a kind other than `start` opted out of validation is still refused as that kind.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the "Deep-link buttons can be followed" requirement states the
  per-kind bot-matching slot in observable terms; the "Only start links are followed, and the
  rest are refused by name" requirement gains the non-empty-`start` precedence rule, the
  companion-parameter precedence rule, the `channel_preview` kind, and the `validate_payload`
  opt-out.

## Impact

- **Code**: `aiogram/test/actors.py` — `_LinkKindPolicy.match_by`, `_addressed_bot`,
  `_path_deep_link`'s query-aware phone branch, `_QUERY_KIND_LOOKUP`'s companion sort,
  `_RESERVED_PATH_KINDS["s"]`, `follow_deep_link(validate_payload=...)`.
- **Tests**: `tests/test_testing/test_deep_links.py` gains the attachment-menu match-by-payload
  suite, the empty-start-does-not-win suite, the companion-precedence suite, the
  channel-web-preview suite, and the `validate_payload` escape-hatch suite.
- **Docs**: `docs/dispatcher/testing.rst`'s Deep links subsection gains the `attach` sentence,
  the non-empty-`start` wording, the companion-precedence sentence, the `channel_preview`
  mention, and the `validate_payload=False` paragraph.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry — the
  toolkit is unreleased, so there is no released behavior to describe a change to.
- **Risk**: `?start=&startapp=y` and `?appname=shop&startapp=ref` now refuse or classify
  differently than before this wave; a suite that happened to rely on the old
  presence-only-`start` or aliases-first reading sees a different (and now spec-correct)
  refusal message. `validate_payload=False` is additive and opt-in, so it changes no existing
  test's behavior.
