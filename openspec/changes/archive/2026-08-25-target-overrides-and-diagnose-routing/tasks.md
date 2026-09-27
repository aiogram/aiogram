# Tasks

## 1. Targeted overrides and the blocked-chat recipe

- [x] 1.1 `MethodMatcher` carries field-equality pairs and predicates, checked against the
      **resolved** method (design D1)
- [x] 1.2 `env.on(Method, **fields)` validates the fields against `model_fields` at
      declaration time, raising `TypeError` naming the unknown ones
- [x] 1.3 `OverrideBuilder.where(predicate)` narrows the matcher in force at the moment it is
      called, without affecting outcomes already declared on the same builder
- [x] 1.4 `OverrideRegistry.take` walks rules in registration order and leaves a
      non-matching rule's `times` budget untouched (design D2)
- [x] 1.5 `env.on(...)` returns an `OverrideHandle`/`OverrideBuilder` whose `.cancel()`
      withdraws exactly the rules it registered, and which works as a context manager
- [x] 1.6 `block_chat` / `env.blocked(chat_id=..., message=...)` registers one rule per
      `DELIVERY_METHODS` entry under one handle, with no `times` budget
- [x] 1.7 `handle_call` records the call before consulting overrides
- [x] 1.8 Tests in `test_overrides.py`: independent targeted blocks, non-consumption of a
      mismatched rule, unknown-field rejection, handle cancellation scoping, the blocked
      recipe across delivery methods, call-log-before-refusal

## 2. Routing diagnostics

- [x] 2.1 `RouteRecord` dataclass: `update_id`, `event_type`, `handled`, `handler`,
      `handler_module`, `router`, `exception`, `handler_path`, `describe()` (design D3)
- [x] 2.2 `_RouteMiddleware` registered on `dispatcher.update.outer_middleware`, inside
      aiogram's own error-handling middleware
- [x] 2.3 `_HandlerMiddleware` registered on every other observer, filling in the winning
      handler/router once filters have passed
- [x] 2.4 `BotTestEnvironment.last_route` / `_open_route` / `_close_route` /
      `_current_route`, cleared at the start of every `feed`
- [x] 2.5 `assert_handled_by(name)` matches by substring of `handler_path`, failing with
      `describe()`
- [x] 2.6 Instrumentation is installed at environment construction and undone in `_restore`
- [x] 2.7 Tests in `test_route_diagnostics.py`: handled/unhandled/catch-all routing, a
      middleware-swallowed update, a swallowed handler exception, reset between updates,
      `assert_handled_by`'s pass and failure paths, instrumentation teardown

## 3. Wait diagnostics and broadcast wait

- [x] 3.1 `wait_for(..., watch=view_or_views)` appends each view's `describe_messages()` to
      the timeout message (design D4)
- [x] 3.2 `wait_for_message_in(chats, predicate=None, description=None, ...)` resolves each
      entry through `BotTestEnvironment.chat`, polls via `newest_match`, and returns
      `chat_id -> Message`
- [x] 3.3 A `wait_for_message_in` timeout names only the chats still missing a match
- [x] 3.4 Tests in `test_waiting.py`: `watch=` on a single chat/topic and on several;
      broadcast wait returns once all match, accepts mixed chat selectors, resolves the
      newest match per chat, and names only the still-missing chats on timeout

## 4. Membership triggers: service message, promote, demote

- [x] 4.1 `_change_membership` gains `service_message`, feeding `new_chat_members` after the
      membership update when `chat.type` is group or supergroup (design D5)
- [x] 4.2 `join()` / `add_bot()` default `service_message=True`; `leave()` / `remove_bot()`
      are unaffected
- [x] 4.3 `promote(subject=None, **rights)` — whole-rights-mask, empty call still promotes,
      owner guard (design D6)
- [x] 4.4 `demote(subject=None)` — clears rights and custom title, keeps `tag`, owner guard
- [x] 4.5 Tests in `test_membership_triggers.py`: service message ordering and content for
      `add_bot()`/`join()`, suppression, private-chat exclusion, `leave()`/`remove_bot()`
      unaffected, promote/demote defaults and named subjects, rights mask exactness, no-op
      rights still promoting, tag surviving demotion, owner guard on both directions

## 5. Reply sugar and click misdirection hint

- [x] 5.1 `send(..., reply_to=message_or_id, ...)` folds into `fields["reply_to_message"]`,
      an explicit `fields` entry still winning
- [x] 5.2 `reply(message_or_id, text=None, ...)` as sugar over `send(reply_to=...)`
- [x] 5.3 `_misdirected_callback_hint` scans every other chat's buttons after the actor's
      own chat fails to find the `callback_data`, appended to the raised message
      (design D7)
- [x] 5.4 Tests in `test_reply_sugar_and_click_hints.py`: reply by object and by id, field
      override precedence, reply chains via `chat.messages[-1]`, the hint naming the
      correct chat, no hint when the button exists nowhere, no false positive for a button
      genuinely missing from the bound chat

## 6. `env.chat` alignment with the actor path

- [x] 6.1 `BotTestEnvironment.chat` opens a declared user's private chat for a bare id
      before falling through to `world.chat`'s raise

## 7. Background task draining

- [x] 7.1 `_running_tasks()` snapshot taken at environment construction
- [x] 7.2 `drain(timeout=1.0)` cancels and awaits every task not in the snapshot, retrieves
      exceptions from cancelled tasks to silence "never retrieved" warnings, and raises
      naming any task still running after the timeout (design D8)
- [x] 7.3 Not called from `dispose()` / `dispose_sync()`
- [x] 7.4 Tests in `test_environment.py`: a task created after construction is cancelled and
      counted; a pre-existing task is left alone; a task that swallows cancellation raises

## 8. Chat-registry assignment now raises

- [x] 8.1 `World.__setattr__`'s `chats` guard raises `WorldLookupError` when the assigned
      value is a live `ChatRegistry` belonging to a different world, naming the ownership
      rule and the explicit `dict(other.chats)` alternative; a plain mapping is still
      wrapped, and a registry already wired to `self` is still left alone by identity
- [x] 8.2 Test in `test_world.py`: `w2.chats = w1.chats` raises and leaves `w1` untouched;
      `w2.chats = dict(w1.chats)` still shares the chat objects, correctly rewired to `w2`

## 9. Documentation

- [x] 9.1 Overrides section: targeting, `.where`, first-match-wins/non-consumption, handle
      `.cancel()`/context manager, the `env.blocked(...)` recipe, call-log-before-override
      ordering
- [x] 9.2 New "Routing diagnostics" section: `last_route`, the handled-vs-handler-is-None
      distinction, `assert_handled_by`
- [x] 9.3 Waits section: `watch=` timeout dumps, `wait_for_message_in` broadcast wait
- [x] 9.4 Membership/actors: `promote()`/`demote()`; `add_bot()`/`join()`'s service message,
      updating the earlier narrative mentions of both as single-update triggers; reply
      sugar; click misdirection hint
- [x] 9.5 `env.chat(user_id)` opening a declared user's private chat
- [x] 9.6 New "Cleaning up background tasks" section: `drain()` and the loop-scoped-cache
      hazard, separate from what `drain()` addresses
- [x] 9.7 API reference: `OverrideHandle`, `MethodMatcher`, `RouteRecord` added alongside
      `OverrideBuilder`

## 10. Spec sync

- [x] 10.1 `bot-testing-environment`: amend overrides matching/targeting, the
      private-chat-on-demand requirement for `env.chat`, the chat-registry requirement to
      raise on a foreign live registry, waits for `watch=`; add requirements for the
      broadcast wait, routing diagnostics, draining, the membership service message,
      promote/demote sugar, reply sugar, and the click misdirection hint

## 11. Release readiness

- [x] 11.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst`
      entry
- [x] 11.2 Full check loop green: `ruff format`, `ruff check --show-fixes --preview aiogram
      examples`, `mypy aiogram`, `pytest tests -q` at 100% coverage for the touched modules
