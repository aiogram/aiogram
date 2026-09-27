## Context

All five findings trace back to the same modeling gap: `_LinkKindPolicy` and
`_QUERY_KIND_LOOKUP` were built as one row per *concept* — one kind, one boolean, one lookup
position — but several of the links https://core.telegram.org/api/links documents carry more
than one signal in the same url, and reading only the signal the row had room for produced a
wrong answer for exactly those links. The fix in each case is the same shape: replace the
single-slot field or fixed order with something that can hold or rank more than one signal,
without touching the kinds that only ever carried one.

## Goals / Non-Goals

**Goals:**

- Let a kind name *which* parsed slot carries the bot it concerns, instead of assuming the
  username slot always does.
- Make `start`'s precedence turn on whether it carries a value, not merely whether the key is
  present.
- Make a query holding both a real format's parameter and a parameter that is *also* another
  format's companion classify by the real format, in both directions Telegram documents.
- Give `t.me/s/<username>` its own kind rather than letting it fall through to a shape it only
  superficially resembles.
- Let a test opt out of the payload-alphabet check without opting out of kind classification.

**Non-Goals:**

- Redesigning `_LINK_KINDS` as anything other than a table of rows — `match_by` and the
  companion sort are both additions to the existing shape, not a replacement for it.
- Simulating the attachment menu, Mini Apps, or any of the other refused kinds. This wave
  changes *which* kind a link classifies as and *whether* the button is this bot's; it does
  not make any new kind followable beyond `start`.

## Decisions

### D1. `match_by` is a slot name, not a second boolean

`addresses_username: bool` could only say "yes, the username slot is the bot's" or "no". It
had no way to say "the bot is somewhere else in this same link" — which is exactly `attach`'s
shape: `t.me/<chat>?attach=<bot>` addresses the chat in the slot every other bot-concerning
kind uses for the bot itself.

`match_by: str` generalizes the field to name *which* slot holds the answer:
`_MATCH_USERNAME` for every kind that already worked, `_MATCH_PAYLOAD` for `attach` alone, and
`""` for the kinds that concern no bot at all (a boost, an invite, a message link — unchanged
from before). `_DeepLink.username` and `_DeepLink.payload` are unchanged NamedTuple fields;
only which one a caller reads changed, and only one caller reads either — see D2.

### D2. `_addressed_bot` is the one place that reads `match_by`

Before this wave, `follow_deep_link` and the automatic scan (`_find_deep_link_url`) each did
their own `deep_link.username.lower() != bot_username.lower()` comparison, hardcoding the
assumption `match_by` now makes explicit. Two call sites making the same assumption is how the
bug shipped in the first place — fixing the assumption in one and not the other would have
left the disagreement standing, just moved.

`_addressed_bot(deep_link)` centralizes the lookup: it reads `match_by`, returns
`deep_link.username`, `deep_link.payload`, or `None` accordingly, and both `follow_deep_link`
and `_find_deep_link_url` now call it and compare against `bot_username` themselves. Neither
site holds its own copy of "which slot means the bot" any more.

One consequence that falls out of D1+D2 together, not a separate design point: the phone
branches of `_path_deep_link` and the `tg://resolve` phone handling both had to start
deferring to the query when `attach` is present, since `t.me/+<phone>?attach=<bot>` is the
`attach` form's third documented shape — the phone number is the chat, exactly like the
username and hash forms, and calling it a phone link first would hide the bot in the query
the same way the original bug hid it behind the username slot.

### D3. Non-empty `start` is checked before the table, not inside it

`_parse_deep_link` already special-cased `start` ahead of `_QUERY_KIND_LOOKUP` for the
precedence rule wave-2 shipped ("`start` wins whenever present"). That check tested
`"start" in query`, which is true for `?start=&startapp=y` — an empty value is still a
present key. The fix narrows the condition to `starts and starts[0]`: a `start` key with an
actual value still short-circuits the table lookup, and a `start` key with none falls through
to it exactly like the aliases and companions do, so `?start=&startapp=y` resolves as
`startapp` and a bare `?start=` still resolves as the bare start it already was (nothing else
in the query to fall through to).

### D4. Companions sort last by a key, not by a second static order — refining the field
report's proposed fix

The field report's first proposed fix was the narrower one: move the alias table
(`_QUERY_KIND_ALIASES`) ahead of the plain kind lookup, since the reported symptom was
`?startapp=x&text=y` reading as `draft` (an alias) when a real client opens the Mini App
(`startapp`, a plain kind) instead. That fix does close the reported case — aliases-first
makes `text` lose to `startapp` — but verifying it against the rest of
`https://core.telegram.org/api/links` turned up the case it breaks: `appname` is itself an
alias (of `miniapp`), so aliases-first also puts `appname` ahead of `startapp`, which is
correct only by coincidence for the reported bug and wrong for
`?appname=shop&startapp=ref` — a real client opens the *named* app `appname` selects, with
`startapp` read as that app's own start parameter, not the bot's plain (unnamed) Mini App.

Aliases-vs-table-rows is the wrong axis: the property that actually decides precedence is
whether Telegram documents the key as also being another format's companion parameter, which
cuts across both the alias table and the plain kind table (`startapp` and `startattach` are
plain kinds *and* companions; `text` is an alias *and* a companion; `appname` is an alias and
*not* a companion). `_COMPANION_QUERY_KEYS` names exactly that set, and
`_QUERY_KIND_LOOKUP` is built by `sorted(..., key=lambda pair: pair[0] in
_COMPANION_QUERY_KEYS)` — a stable sort, so within each half every kind's own table row still
precedes its alias, which is where `attach` sitting above `startattach` in `_LINK_KINDS`
continues to decide the one tie inside the non-companion half. A companion key with nothing
else in the query still falls through to its own row, since it is only ever skipped in favor
of something else present.

### D5. `channel_preview` is a reserved path segment, not a `miniapp` special case

`t.me/s/<username>` used to reach `_path_deep_link`'s final branch — one path segment after a
single-letter first segment, which matches the direct-Mini-App shape
(`t.me/<bot>/<short_name>`) exactly, and returned `_DeepLink(username="s", kind="miniapp",
payload=username)`. Fixing this inside the Mini-App branch would mean special-casing a
single-letter username there, which reads as an arbitrary carve-out with no explanation for why
`s` specifically.

`_RESERVED_PATH_KINDS["s"] = "channel_preview"` fixes it at the point the toolkit already
reserves segments Telegram never lets be a username (`joinchat`, `share`, `boost`, …): `s` is
excluded from real usernames by Telegram's own rules for the same reason those are, so it
belongs in the same table, checked before the Mini-App path shape is tried at all. This also
keeps `t.me/<username>/s/<n>` (the *story* shape, `/s/` as the *second* segment) correctly
unaffected — that branch is only reached once the reserved-segment check on the *first*
segment has already passed.

### D6. `validate_payload` gates one function call, not a branch in classification

The escape hatch could have been modeled as a third classification outcome ("valid start",
"invalid-but-permitted start", "invalid start") threaded through `_LINK_KINDS`, but that would
let `validate_payload=False` change *which kinds are followable* if it were ever misapplied —
exactly the failure mode the design has to rule out, since the flag exists to loosen one
specific production-realism check, not the classifier.

Instead `follow_deep_link` calls `_require_valid_start_payload` conditionally —
`if validate_payload: _require_valid_start_payload(url, deep_link.payload)` — after
classification and the `followable` check have already run. A `startapp` link opted out of
payload validation still hits the `followable` check first and is refused as `startapp`,
never reaching the payload check at all; the flag only ever removes the one check, on the one
kind (`start`) that reaches it.

## Testing

- `tests/test_testing/test_deep_links.py`: an attachment-menu suite parametrized over all four
  documented `attach` shapes (`t.me/<chat>?attach=<bot>`, `t.me/+<phone>?attach=<bot>`, and
  their `tg://resolve` twins) asserting the button is refused as the chat's-attach-menu link
  and not as "not to this bot", that the automatic scan surfaces it as a candidate, and that
  `attach` wins over a `startattach` parameter it carries alongside it.
- A start-precedence suite covering `?start=&startapp=y` (and its reordering, and the `tg:`
  form) refusing as `startapp`, alongside the unchanged non-empty-`start`-wins cases.
- A companion-precedence suite covering `?startapp=x&text=y` (both orders), `?startattach&text=y`,
  `?text=hi&profile`, `?startgroup=g&text=hi`, and `?appname=shop&startapp=ref` — the case D4's
  refinement exists for — each asserting the owning format's own rejection message, plus each
  companion alone still naming its own kind.
- A `channel_preview` suite: `t.me/s/<username>`, `t.me/s/<username>/<post>` and bare `t.me/s`
  refused as a web-preview link with `"Mini App"` absent from the message; the scan ignoring
  such a button entirely (it addresses no bot); and `t.me/<username>/s/<n>` still classifying
  as a story link.
- A `validate_payload` suite: an out-of-alphabet payload (base64 padding, dots, over-length)
  replayed as-is with `validate_payload=False` through both the explicit-target and scan forms;
  the default still refusing the same payload; and `validate_payload=False` on a non-`start`
  kind still refusing that kind rather than following it.
