# Tasks

## 1. Trigger-scoped routing diagnostics

- [x] 1.1 `_ROUTE_IN_FLIGHT` context variable replaces any per-environment stack of "the
      record in flight," so concurrent feeds in separate tasks stay isolated (design D1)
- [x] 1.2 `BotTestEnvironment.trigger()` context manager: re-entrant, clears the scope's
      record list on outermost entry, restores nothing on exit but the depth counter
      (design D2)
- [x] 1.3 A bare `feed` outside any explicit `trigger()` block and not nested inside a
      running handler opens a scope of its own
- [x] 1.4 Every multi-update actor trigger (`join()`, `add_bot()`, `promote()`, `demote()`)
      wraps its updates in one `trigger()` scope
- [x] 1.5 `routes` exposes every record of the current scope in completion order
- [x] 1.6 `last_route` is the newest **handled** record in the scope, falling back to the
      newest record of any kind only when nothing was handled
- [x] 1.7 `assert_handled_by` scans every record of the scope and dumps all of them,
      including captured exceptions, on failure
- [x] 1.8 Tests in `test_route_diagnostics.py::TestTriggerScope`: a join's handler is found
      whichever of the two updates it claimed; `routes` holds both records

## 2. Blocked-chat recipe coverage and addressing symmetry

- [x] 2.1 `BLOCKED_METHODS` = `DELIVERY_METHODS` plus the `editMessage*` family,
      `stopMessageLiveLocation`, `stopPoll`, `setMessageReaction`, the pin/unpin trio, with
      `deleteMessage`/`deleteMessages` documented as a deliberate exclusion (design D3)
- [x] 2.2 `block_chat` registers one rule per `BLOCKED_METHODS` entry per addressing field it
      actually has (`chat_id`, and `user_id` where present), covering `sendGift`
- [x] 2.3 `ADDRESSING_FIELDS` names the chat-addressing fields (`chat_id`, `from_chat_id`,
      `sender_chat_id`) eligible for username resolution
- [x] 2.4 `MethodMatcher.matches` accepts an optional resolver; on a plain-equality
      mismatch on an addressing field, both sides are resolved through the world before a
      second comparison (design D4)
- [x] 2.5 `BotTestEnvironment.resolve_addressing` is the resolver supplied to every match
- [x] 2.6 Tests in `test_overrides.py::TestBlockedCoversMoreThanDelivery`: editing, pinning,
      reacting in a blocked chat fail; a gift addressed by `user_id` is blocked; deleting is
      unaffected; an unrelated chat is untouched
- [x] 2.7 Tests in `test_overrides.py::TestUsernameAddressing`: a block/rule declared by id
      catches a call by username and vice versa; the leading `@` is optional on either side;
      another chat's username is not caught; an unresolvable username matches nothing

## 3. Never-fired override diagnosis

- [x] 3.1 `OverrideRule.fired` counter, incremented by `OverrideRegistry.take` on every
      match (design D5)
- [x] 3.2 `OverrideRegistry.unfired()`/`describe_unfired()`
- [x] 3.3 `BotTestEnvironment.assert_overrides_consumed()` raises naming every unfired rule
- [x] 3.4 The same listing is appended to `wait_for` and `wait_for_message_in` timeouts
- [x] 3.5 Tests in `test_overrides.py::TestNeverMatchedOverridesAreNamed`: the assertion, a
      condition-wait timeout and a broadcast-wait timeout all name a never-fired override; a
      fired or a cancelled rule is not named; a predicate rule describes itself by name

## 4. Per-chat registry ownership

- [x] 4.1 `ChatRegistry.__setitem__` refuses a chat whose `.world` already names a different
      world, whatever container it arrived through (design D6)
- [x] 4.2 `World.__setattr__`'s message no longer recommends `dict(other.chats)`; it points
      at detaching the chat (`chat.world = None`) or rebuilding from the blueprint instead
- [x] 4.3 A fresh chat (`.world is None`) is still adopted normally; a chat already wired to
      *this* world is left alone by identity
- [x] 4.4 Tests in `test_world.py`: assigning a foreign live registry is refused;
      `dict(other.chats)` does not get past the refusal; a detached chat can be moved; a
      fresh chat is adopted; re-registering a chat in its own world is a no-op; a deep copy
      of a world keeps its chats wired to the copy

## 5. Promote/demote validation and parameter symmetry

- [x] 5.1 `_validate_rights` rejects an unknown right with `TypeError`, naming the valid
      ones, mirroring `overrides._validated_fields` (design D7)
- [x] 5.2 `promote(subject=None, *, data=None, **rights)` / `demote(subject=None, *,
      data=None)` — both take dispatcher data through `data=` (design D8)
- [x] 5.3 The owner guard on both raises `WorldLookupError`, not `ApiRejection`, since a
      trigger arranges the world directly (design D9)
- [x] 5.4 Tests in `test_membership_triggers.py`: a misspelled right raises `TypeError`
      naming the valid ones; `data=` reaches the handler on both triggers; the owner guard
      raises `WorldLookupError` in both directions

## 6. `drain()` first-asynchronous-action snapshot and failure reporting

- [x] 6.1 The protected-task snapshot, taken at construction, is extended again at this
      environment's first asynchronous door (`feed` or `handle_call`), run-once (design D10)
- [x] 6.2 A task ending with anything other than the sent `CancelledError` is collected and
      raised as `DrainedTaskError`, naming every such task with the first traceback chained
- [x] 6.3 A task that outlives its cancellation still raises `WaitTimeoutError`, distinct
      from a task that failed of its own accord
- [x] 6.4 `DrainedTaskError` (`errors.py`) and its export from `aiogram.test`
- [x] 6.5 Tests in `test_environment.py`: a task alive at the first `feed` is spared even
      though the construction-time snapshot was empty; a call also extends the protection; a
      task that fails on its own, or while being cancelled, surfaces as `DrainedTaskError`
      with its traceback chained; a stuck task is reported as `WaitTimeoutError`, together
      with any failed task found alongside it

## 7. Documentation

- [x] 7.1 Blocked-chat recipe section: full `BLOCKED_METHODS` coverage, the documented
      exclusion, `user_id` addressing, `@username` resolution, `BLOCKED_BY_USER`
- [x] 7.2 New "An override that never fires" subsection: `assert_overrides_consumed()`
- [x] 7.3 Routing diagnostics section: trigger scope, `trigger()`, `routes`, the corrected
      `assert_handled_by` failure wording, a `join()`-asserts-cleanly example
- [x] 7.4 Waits sections: the shared `as_views` vocabulary named explicitly; broadcast-wait
      raising-predicate reporting; the unfired-override footer cross-referenced from both
      wait sections
- [x] 7.5 Background-tasks section: the first-asynchronous-action snapshot extension,
      `DrainedTaskError` vs `WaitTimeoutError`
- [x] 7.6 Promoting/demoting section: `data=`, the `TypeError` on an unknown right, the
      owner-guard example corrected from `ApiRejection` to `WorldLookupError`
- [x] 7.7 Deep-links section: the boost-link example made copy-pasteable by posting the
      button first
- [x] 7.8 API reference: `DrainedTaskError`, `NoFileContentError` added alongside the
      existing error autoclasses

## 8. Spec sync

- [x] 8.1 `bot-testing-environment`: amend routing diagnostics to trigger scope; amend the
      overrides requirement for blocked-recipe breadth and addressing-field resolution; add
      the never-fired-override assertion and cross-reference it from both wait
      requirements; amend the chat-registry requirement to per-chat enforcement; amend the
      promote/demote requirement for rights validation and `data=`; amend the
      background-task-draining requirement for the snapshot extension and drained-task
      failure reporting

## 9. Release readiness

- [x] 9.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst`
      entry
- [x] 9.2 Full check loop green: `ruff format`, `ruff check --show-fixes --preview aiogram
      examples`, `mypy aiogram`, `pytest tests -q` at 100% coverage for the touched modules
