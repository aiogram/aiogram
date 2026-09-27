## Why

An internal review round replayed each wave-4 feature — targeted overrides, routing
diagnostics, promote/demote sugar, background-task draining, the registry ownership guard —
against the multi-update, multi-field-addressing scenarios the toolkit's own field report had
already surfaced elsewhere, and found ten confirmed gaps, each with a runnable repro:

- `last_route`/`assert_handled_by` only ever looked at the single most recently completed
  route record. `member.join()` in a group feeds two updates — the membership transition and
  the group's own `new_chat_members` announcement — and a bot that correctly handled the
  first while ignoring the second failed `assert_handled_by("on_user_joined")` anyway,
  because the service message was the last thing routed and nobody claimed it.
- `env.blocked(...)` only reached `DELIVERY_METHODS`. A bot whose failed-send recovery path
  edits its previous message, unpins it, or clears a reaction sailed through a block that
  only knew about `Send*`/`Copy*`/`Forward*`, so a test of that recovery path proved nothing.
  `sendGift` addresses its recipient by `user_id` rather than `chat_id`, and a block keyed on
  `chat_id` alone let a gift to a blocked user through untouched.
- Chat-addressing fields were compared by plain equality, so a rule declared for a chat's
  numeric id silently never matched a call the bot addressed as `@username`, and vice versa —
  a block or an override was invisibly absent for a bot using the other spelling.
- Nothing told a test that a declared override never fired at all. A one-digit-off chat id
  in a field filter registered cleanly, matched nothing, and the failure surfaced far from
  the actual mistake — "the bot sent the message it was supposed to fail to send."
- The chat-registry ownership guard lived only in `World.__setattr__`, and its own error
  message recommended the exact bypass that defeated it: `world.chats = dict(other.chats)`
  unwraps the registry, passes that one check, and then silently rewrites `chat.world` on
  the donor's own chats one item at a time.
- `promote(**rights)` accepted any keyword at all — a misspelled `can_pin_message` (missing
  the trailing `s`) was silently dropped, and the test failed later on the bot's own
  "missing right" branch with no clue which right or why. `promote`'s rights and `demote`'s
  dispatcher data occupied the same keyword position for two different purposes, a trap for
  the natural next edit of adding the other trigger's own dispatcher data.
- `drain()`'s protected-task snapshot was taken once, at construction, when the (synchronous)
  `bot_env` fixture usually has no event loop running yet at all — so the snapshot was empty,
  and the first test in a session to call `drain()` silently killed a session-scoped async
  fixture's own background worker, breaking every later test in the session. Separately, a
  task that failed on its own during drain was swallowed or conflated with one that merely
  failed to finish in time, either way losing the real traceback.

## What Changes

- **Routing diagnostics reason about a trigger scope, not a single update.** A `ContextVar`
  (not a stack on the environment) tracks the record in flight per task, so concurrent and
  nested feeds stay isolated. `BotTestEnvironment.trigger()` groups every update fed inside
  it into one scope — used internally by every multi-update actor trigger — and a bare feed
  outside any explicit block opens a scope of its own. `routes` lists every record of the
  current scope; `last_route` is the newest **handled** one, falling back to the newest
  record only when nothing in the scope was handled; `assert_handled_by` scans and dumps the
  whole scope on failure.
- **`env.blocked(...)` covers what a real block actually stops.** The new
  `BLOCKED_METHODS` extends `DELIVERY_METHODS` with the `editMessage*` family,
  `stopMessageLiveLocation`, `stopPoll`, `setMessageReaction` and the pin/unpin trio —
  documenting `deleteMessage`/`deleteMessages` as a deliberate exclusion — and registers a
  rule per addressing field a method actually has (`chat_id` and, where present, `user_id`),
  which is what makes `sendGift` block correctly.
- **Chat-addressing fields resolve symmetrically.** `MethodMatcher.matches` accepts an
  optional world resolver; when given one, `chat_id`/`from_chat_id`/`sender_chat_id` are
  resolved on both sides of a mismatched comparison, so a rule declared with one spelling of
  a chat still answers a call made with the other, in either direction.
- **A never-fired override is diagnosable.** `OverrideRule` tracks how many calls it
  answered; `env.assert_overrides_consumed()` fails naming every declared override that
  never matched anything, and the same listing is appended to every `wait_for`/
  `wait_for_message_in` timeout.
- **Registry ownership is enforced where the mutation actually happens.**
  `ChatRegistry.__setitem__` refuses a chat that already belongs to a different world,
  whatever container it arrived through — closing the `dict(other.chats)` bypass that used
  to be the guard's own recommended workaround. `World.__setattr__`'s guard remains as the
  fast path for the common whole-registry mistake, and its message no longer recommends the
  bypass.
- **`promote()`'s rights are validated like an override's field filters.** An unknown
  keyword raises `TypeError` naming the valid rights. Both `promote()` and `demote()` now
  take dispatcher data through the same keyword-only `data=` parameter, so the two triggers
  agree on what that position means. The owner guard on both raises `WorldLookupError` — a
  setup error, since a trigger arranges the world directly rather than going through the
  intercepted call path.
- **`drain()`'s protection covers a fixture the environment could not see running yet.** The
  protected-task snapshot is extended again at this environment's first asynchronous action
  (the first `feed` or intercepted call), not only at construction, which is what spares a
  session-scoped fixture's own worker regardless of whether a loop existed when the
  environment was built. A drained task that failed on its own now surfaces as
  `DrainedTaskError`, with its traceback chained, distinct from a task that merely outlived
  its cancellation (`WaitTimeoutError`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: routing diagnostics now scope to a trigger rather than a single
  update; the blocked-chat recipe's coverage and addressing-field resolution are specified;
  a new assertion for never-fired overrides is added, referenced from the wait timeout
  requirements; the chat-registry requirement now specifies per-chat enforcement rather than
  only whole-assignment enforcement; the promote/demote requirement gains rights validation
  and the shared `data=` parameter; the background-task-draining requirement specifies the
  first-asynchronous-action snapshot extension and the drained-task-failure behavior.

## Impact

- **Code**: `environment.py` (`_ROUTE_IN_FLIGHT` context variable, `trigger()`, `routes`,
  `last_route`, `assert_handled_by`'s scope-wide scan, `_protect_running_tasks`, `drain`'s
  `DrainedTaskError` path, `resolve_addressing`); `overrides.py` (`BLOCKED_METHODS`,
  `ADDRESSING_FIELDS`, `MethodMatcher.matches`'s resolver, `OverrideRule.fired`,
  `OverrideRegistry.unfired`/`describe_unfired`, `block_chat`'s per-addressing-field
  registration); `world.py` (`ChatRegistry.__setitem__`'s per-chat ownership check,
  `World.__setattr__`'s updated message); `actors.py` (`_validate_rights`, `promote`'s and
  `demote`'s shared `data=` parameter, the owner guard's `WorldLookupError`); `errors.py`
  (`DrainedTaskError`); `__init__.py` (the new names exported).
- **Tests**: `test_route_diagnostics.py` (`TestTriggerScope`), `test_overrides.py`
  (`TestBlockedCoversMoreThanDelivery`, `TestUsernameAddressing`,
  `TestNeverMatchedOverridesAreNamed`), `test_world.py` (per-chat ownership scenarios),
  `test_membership_triggers.py` (rights validation, `data=`, owner guard), `test_waiting.py`
  (broadcast raising-predicate and unfired-override reporting), `test_environment.py`
  (first-asynchronous-action protection, `DrainedTaskError`), `test_errors.py`
  (`DrainedTaskError`'s own shape), `test_files.py` (minor fixture alignment).
- **Docs**: `docs/dispatcher/testing.rst` — the blocked-chat recipe section documents its
  full coverage, the exclusions, `user_id` addressing and `BLOCKED_BY_USER`; a new "An
  override that never fires" subsection documents `assert_overrides_consumed()`; the routing
  diagnostics section documents trigger scope; the waits sections document the shared
  `as_views` vocabulary and the unfired-override footer; the background-tasks section
  documents the first-asynchronous-action snapshot and `DrainedTaskError`; the
  promoting/demoting section documents `data=` and rights validation, and corrects the
  owner-guard example's exception type; the deep-links boost example is made
  copy-pasteable; the API reference gains `DrainedTaskError` and `NoFileContentError`.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry — the
  toolkit is unreleased, so there is no released behavior to describe a change to.
- **Risk**: the registry-ownership change is a further behavioral tightening on top of wave
  4's — code that relied on the `dict(other.chats)` workaround the previous guard's own
  message recommended now sees `WorldLookupError` there too. That workaround was itself the
  unresolved half of the bug wave 4 set out to fix, so the tightening is the fix completing,
  not a new restriction.
