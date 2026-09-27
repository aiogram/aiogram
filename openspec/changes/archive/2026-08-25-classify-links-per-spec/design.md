## Context

`_LINK_KINDS` had grown organically: a kind was added when a test scenario needed it refused
correctly, not by working through Telegram's own link reference. That is how `t.me/$<slug>`
ended up parsing as a `start` link to `@$AbCdEfGhIj` — nobody had written a test with an
invoice link on a button, so the path classifier never had to say what one was, and the
fallback ("one path segment, not `+something`, not `joinchat`") quietly treated it as a
username instead. https://core.telegram.org/api/links documents roughly two dozen link
formats; auditing the table against it, kind by kind, is what this change is.

## Goals / Non-Goals

**Goals:**

- Every link format the spec documents gets its own `kind` and its own rejection wording,
  naming what a real client does with it.
- No format is silently absorbed into a wrong neighbor (invoice into start, phone into invite,
  a `tg://` host into "not a Telegram link").
- Where the toolkit already models the action a link only opens a screen for, the rejection
  says so.
- A `start` payload outside what Bot API deep linking can deliver is refused before it reaches
  a handler.

**Non-Goals:**

- Simulating any of the newly-recognized formats. `boost()`, `pay()` and `pre_checkout_query()`
  already model the actions an invoice or boost link opens a screen for; nothing here adds
  simulation for Mini Apps, stories, business chats or the rest — they are still refused, just
  refused correctly.
- Re-deciding the precedence rule (`start` wins alongside a start-ish parameter) or the
  private-chat-on-demand rule. Both are unchanged; this change only touches classification and
  payload validation.
- A general link-parsing library. `_parse_deep_link` stays specific to the shapes `t.me` and
  `tg://` use; there is no reason for it to handle urls no Telegram client would produce.

## Decisions

### D1. One row per documented kind, two constructors for the two families

Every kind Telegram documents either addresses a bot by username (`start` and its siblings) or
addresses something else — a chat, a slug, an app screen (`phone`, `invoice`, `service_path`,
...). `_bot_link(reason, instead=...)` and `_foreign_link(reason, instead=...)` build the
`_LinkKindPolicy` for each family with consistent wording, so a new row is one call rather than
a hand-written `rejection=` string that might drift from its siblings'. `addresses_username`
records which family a row belongs to as a fact `follow_deep_link` reads, not something it
re-derives from the kind's name.

### D2. The path shape is classified exhaustively, not just enough to reach the next test

`_path_deep_link` walks every path shape the spec documents, in the order that resolves
ambiguity correctly: `+` before anything else (phone vs. invite hash), `$` for an invoice,
then the reserved-segment table, then the shapes that need a second segment (a story, a
message, a direct Mini App). The old version stopped at "does it start with `+`, is it
literally `joinchat`, does it have more than one segment" — which is exactly the set the first
PoC's test scenarios needed and no further, and it is exactly why `t.me/$slug` fell through to
"the segment is the username". Classifying every documented shape, rather than the shapes a
test happened to already cover, is the point of auditing against the spec instead of against
the test suite.

### D3. Phone and invite are told apart the way Telegram tells them apart

`t.me/+<digits>` and `t.me/+<hash>` share a prefix and nothing else — one addresses a phone
number, the other a private chat, and Telegram's own clients disambiguate by whether the tail
is all digits. `_PHONE_NUMBER.fullmatch(rest)` is that same rule, applied once in
`_path_deep_link` and mirrored for the `tg://resolve?phone=` form. Folding them into one
`invite` kind (the old behavior) was not a simplification — it was a wrong claim about what
the link does, stated confidently.

### D4. A `tg://` host the table does not enumerate is `service_path`, not "not a link"

`_TG_HOST_KINDS` lists the hosts worth telling apart — `join`, `boost`, `invoice`, and so on —
because the toolkit already has something specific to say about each (an alias of the `t.me`
kind with the same name). Any other host — `tg://settings`, `tg://stars`, a host Telegram adds
after this table was written — falls back to `service_path`. That fallback is deliberately
honest rather than deliberately silent: it does not enumerate every app screen Telegram might
ever add, but it also never claims the url is not a Telegram link, which the old `return None`
for any non-`resolve` host did for every one of them.

### D5. Two rejections point at the trigger instead of only naming the screen

`invoice` and `boost` are the two kinds where "what a real client does with it" has an exact
counterpart already in the toolkit: an invoice link opens a payment form, which `pay()` and
`pre_checkout_query()` already model end to end; a boost link opens the boost screen, which
`boost()` already delivers as `chat_boost`. Naming the trigger in the rejection turns "this
isn't simulated" into "here's how to test it", for the two kinds where that sentence is true.
It is not extended to every kind — a Mini App genuinely has no toolkit-side model to point at,
and saying so would be a broken pointer, not a correction.

### D6. Payload validation runs after every other check, not instead of them

`_require_valid_start_payload` is called from `follow_deep_link` only once `deep_link.kind` is
confirmed to be `start` and the username matches — a mistargeted or wrong-kind link should be
refused for *that* reason, not for an incidentally-invalid payload it happens to also carry.
The automatic scan goes through the same `follow_deep_link` call for its chosen candidate, so a
`start` link with a broken payload is refused with the payload rule even when the scan found
it, rather than being treated as followable and only failing later.

The alphabet (`[A-Za-z0-9_-]{1,64}`) comes directly from
https://core.telegram.org/bots/features#deep-linking, cited in both the code comment and the
rejection message, the same way the link-kind classification cites
https://core.telegram.org/api/links.

## Risks / Trade-offs

- **`service_path` and `extra_path` are still catch-alls** → deliberately so: Telegram
  documents more app screens and service paths than a test toolkit has reason to name
  individually, and the two fallbacks say what they are (a service link, a link with
  unrecognized extra path segments) without pretending to enumerate every one.
- **The rejection wording is now longer for several kinds** (pointing at `pay()`, `boost()`,
  `send()`) → each pointer only appears where the toolkit has something specific for the test
  to do next; the previous "not simulated" was true but did not tell a reader where to look.
- **Payload validation is a new refusal a passing test could hit** → only for a payload a real
  client could never have produced, which means the test was passing on a broken button before
  this change, not on a working one.

## Migration Plan

Additive to what a test can express, corrective to what refusals say. No previously-followable
link becomes unfollowable, and no previously-refused link becomes followable — `start` was
already the only followable kind. A test that asserted on the exact wording of an old generic
rejection (`"a link with extra path segments"`, `"not a Telegram deep-link url"` for a
non-`resolve` `tg://` host) needs its `match=` updated to the format-specific message; the
toolkit is still unreleased, so no downstream test suite depends on the old wording.

## Open Questions

None — the audit was closed out against https://core.telegram.org/api/links directly.
