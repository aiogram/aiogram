## 1. The polling core

- [x] 1.1 Add `aiogram/test/waiting.py` with `poll_until(predicate, *, timeout, interval,
      describe_timeout)` (design D1)
- [x] 1.2 Check once before sleeping and once after the deadline passes
- [x] 1.3 Clamp each sleep to what is left of the timeout (design D2)
- [x] 1.4 Accept a synchronous predicate or one returning an awaitable, and return whatever
      truthy value it produced (design D3)
- [x] 1.5 Add `describe_callable` for identifying a predicate in a failure message
- [x] 1.6 Add `WaitTimeoutError(TimeoutError)` to `aiogram/test/errors.py` and export it from
      `aiogram.test` (design D7)

## 2. Waiting for a condition

- [x] 2.1 Add `BotTestEnvironment.wait_for(predicate, *, timeout, interval, description)`
- [x] 2.2 Build the failure message lazily, naming the description when given and the predicate
      otherwise (design D7)
- [x] 2.3 Tests: an already-true condition returns without waiting; a change made by a
      background task is picked up; the truthy value is returned; an async predicate is
      awaited; the timeout raises and identifies the predicate; a coarse interval does not
      overshoot the timeout; a predicate with no name falls back to its repr

## 3. Waiting for a message

- [x] 3.1 Add `ChatState.wait_for_message(predicate=None, *, timeout, interval)`, matching
      against every message the chat holds, newest first (design D4)
- [x] 3.2 Add `TopicState.wait_for_message(...)` over the topic's own filtered view, passed as a
      callable so the view is recomputed on every pass (design D6)
- [x] 3.3 Share one implementation between the two, differing only in the view, the noun and how
      the failure names where it waited
- [x] 3.4 Add `describe_message` / `describe_messages` and enumerate the view in the timeout
      message, truncating long text
- [x] 3.5 Tests: a message already there matches immediately; one sent by a background task
      matches; the newest match is returned; no predicate matches any message; the timeout lists
      what the chat holds; an empty chat says so; a message without text is still identified; a
      long text is truncated; the returned message is mounted and usable

## 4. A predicate that raises

- [x] 4.1 Treat an exception from the predicate as "does not match" rather than failing the wait
      (design D5)
- [x] 4.2 Keep what it raised for the most recent pass and report it, per message id, in the
      timeout message
- [x] 4.3 Tests: a service message does not break a `m.text.startswith(...)` wait; the timeout
      reports what the predicate raised and where; a predicate that always raises still fails
      with its real cause; the same holds for a topic

## 5. Topic scoping

- [x] 5.1 Add `TopicState.label` so a failure names the topic — the General topic by name, any
      other by id and title, with its chat
- [x] 5.2 Tests: a message posted into the topic matches; a message in a sibling topic does not
      satisfy the wait; the General topic names itself; a hand-built topic still names itself

## 6. Documentation

- [x] 6.1 Add a "Bots with background tasks" section to `docs/dispatcher/testing.rst`
- [x] 6.2 Show both helpers, the topic-scoped form, and what the failure message contains
- [x] 6.3 Explain the raising-predicate rule and that the cause still surfaces
- [x] 6.4 State plainly that no fake clock ships here, and that a time-control library is a
      starting point rather than a promise
- [x] 6.5 Add the wait methods and `WaitTimeoutError` to the API reference; build docs and fix
      any new warnings

## 7. Release readiness

- [x] 7.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry
- [x] 7.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview
      aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q
      --cov=aiogram --cov-report=term-missing` at 100%
