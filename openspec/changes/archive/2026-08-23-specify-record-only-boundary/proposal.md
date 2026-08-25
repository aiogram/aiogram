## Why

`aiogram.test` models 103 of the Bot API's 185 methods. The other 82 are recorded and
answered with a synthesized result — which is documented — but *which* surfaces those are,
and whether each is a considered decision or an oversight, is written down nowhere.

That distinction matters more than it looks. The research behind the toolkit classified
roughly 37 methods as record-only **forever** (the call log is the entire useful assertion)
and a handful of clusters as **deferred** (worth modeling when demand appears). Today both
look identical from outside: absent. A contributor cannot tell whether `setPassportDataErrors`
is unmodeled because it should be, or because nobody got to it — so the honest answer to
"should I model this?" is currently "read the git history of a planning document".

There is also nothing stopping the modeled set from drifting into the record-only surfaces
by accident, one well-meaning pull request at a time.

## What Changes

- **The record-only surfaces are named in the spec**, grouped by why: ephemeral messages
  and drafts, managed bots, verification, profile media, webhook configuration and
  `getUpdates`, suggested posts, Telegram Passport, mini-app handoffs, and sender-chat
  bans. Each group carries its reason — no state a test reads back, media processing, or a
  layer the toolkit deliberately does not drive.
- **The deferred clusters are named separately** — stars and gifts, sticker sets, stories,
  business account profile — as candidates rather than refusals, so "not yet" is
  distinguishable from "no".
- **A guard test** asserts the modeled registry and the record-only list do not overlap, so
  modeling one of these surfaces is a deliberate edit to both rather than a silent
  addition.
- **The documentation** gains the same two lists, so a user can see at a glance whether the
  method they care about is modeled, deliberately not, or waiting for demand.

No behavior changes. No code changes beyond the guard test and its list.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the requirement covering unmodeled methods is extended to
  state that the record-only surface is an explicit, enumerated decision rather than the
  absence of one.

## Impact

- **Code**: none, beyond a module-level list of record-only method types that the guard
  test reads. It lives next to the registry it guards.
- **Tests**: one guard test in `tests/test_testing/`.
- **Docs**: a "What stays record-only" section in `docs/dispatcher/testing.rst`.
- **Changelog**: none — nothing user-visible changes. This is a `skip news` change, or a
  line folded into the toolkit's existing entry if it has not shipped yet.
- **Risk**: the list is hand-maintained and will fall behind a Bot API bump that adds a
  method belonging to one of these families. Mitigated by the guard being an
  *anti*-overlap check rather than a completeness check: a new unlisted method is simply
  unmodeled-and-unlisted, which is the existing default, not a build break.
