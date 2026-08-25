## Context

The toolkit's contract is that a trigger returns when the dispatcher is done with the update.
For a bot whose handlers do all their work inline, that is the whole story and no waiting is
needed. For a bot with an engine of its own it is only the beginning: the handler schedules,
returns, and the world keeps changing.

Nothing in the toolkit was wrong about this — it simply had no vocabulary for it, so every user
would write the same loop, and write it slightly differently.

## Goals / Non-Goals

**Goals:**

- One obvious way to wait, in the two shapes tests actually need: a condition, and a message.
- A failure that shows what *did* happen, not just that nothing did.
- The timeout means what it says.

**Non-Goals:**

- **A fake clock.** Controlling time is a whole design of its own, it interacts with every
  `asyncio.sleep` in the bot under test, and getting it wrong is worse than not having it. The
  documentation points at time-control libraries as a starting point and is explicit that the
  combination has not been exercised here.
- Waiting on API *calls* rather than state. `env.calls` is already a synchronous record, and a
  call the bot has not made yet is indistinguishable from one it never will — the condition a
  test really wants is almost always about the world.
- Cancelling or draining the bot's background tasks. That is the test's own business, and
  reaching into it would make the toolkit responsible for a lifecycle it does not own.

## Decisions

### D1. One polling core, in a module of its own

`poll_until` lives in `aiogram/test/waiting.py` rather than on the environment, because both
ends need it and `aiogram.test.world` must not import `aiogram.test.environment` — the
dependency runs the other way.

It checks the predicate **once before any sleeping**, so an already-satisfied wait costs
nothing, and **once more after the deadline has passed**, so a change landing exactly on the
deadline still counts.

Sleeping is what makes the whole thing work at all: the bot's background tasks only run while
the test yields to the event loop.

### D2. Sleeps are clamped to what is left of the timeout

A loop that sleeps a full interval and then checks overshoots by up to one interval, so
`timeout=1.0, interval=0.5` could take 1.5 seconds. Clamping makes `timeout` the promise it
reads as, and it is one `min()`.

### D3. The predicate returns the value, not just a verdict

`wait_for` hands back whatever truthy value the predicate produced, so it both tests and
fetches:

```python
await env.wait_for(lambda: game.phase is Phase.NIGHT)
victim = await env.wait_for(lambda: game.find_victim())
```

Two helpers — one returning `bool`, one returning a value — would be the same code twice, and
the truthiness rule is the one Python users already expect from `any`, `filter` and `or`.

The predicate may be synchronous or return an awaitable, because a test may need to wait on a
coroutine reading the state under test. `inspect.isawaitable` on the result covers both without
the caller declaring which it is.

### D4. `wait_for_message` matches everything the chat holds, newest first

Waiting only for messages arriving *after* the call would look tidier and would be a race: the
send being waited for may already have happened by the time the wait starts, in which case the
test hangs until it times out on a condition that was true all along.

Matching against the whole list makes an already-satisfied wait return immediately, which is the
same rule `poll_until` applies to any predicate. The scan runs newest-first so several matches
resolve to the newest one — a test waiting for "the reply" wants the last one.

### D5. A raising predicate is "no match", and the exceptions surface in the timeout

A chat holds messages of every shape. The natural `lambda m: m.text.startswith("Night")` blows
up on the first service message — `forum_topic_created`, a pin, a title change — whose `text` is
`None`, and that message has nothing to do with what the test is asking about.

So a raising predicate does not fail the wait. But swallowing the exception outright turns a
genuinely buggy predicate into a silent timeout, so the exceptions are kept for the *most
recent* pass and reported in the failure message, per message id. A predicate that always raises
therefore still fails visibly, with its real cause named.

Keeping only the most recent pass is deliberate: the interesting question is what the predicate
does to the chat as it stands at the deadline, not a transcript of every attempt.

### D6. A topic waits over a callable view, not a captured list

`TopicState.messages` is a filtered view over the chat's single message list, recomputed on
every read. The wait therefore takes a *callable* returning the view: capturing the list once
would wait on a snapshot taken before the message being waited for arrived — a wait that can
never succeed.

That is also what makes the topic wait the same implementation as the chat wait, with only the
view, the noun and the "where" differing.

### D7. `WaitTimeoutError` subclasses `TimeoutError`

A test that catches the generic timeout — `pytest.raises(TimeoutError)` — catches this too, and
a reader who has never met the toolkit's own type still knows what happened. The message is
assembled by the caller, which is the only side that knows what was being waited for and what
the world holds instead.

`describe_timeout` is a callable rather than a string, so enumerating a chat's messages costs
nothing on the happy path.

## Risks / Trade-offs

- **Real-time slowness** → a bot whose engine sleeps for thirty seconds makes a test that waits
  on it take thirty seconds. Named in the documentation, with time-control libraries suggested
  as a starting point and explicitly not promised.
- **A wait hides a missing `await`** → a test that should have awaited something now passes by
  polling instead. Accepted: the alternative is that tests of asynchronous bots are simply
  flaky.
- **"No match" swallowing a real bug** → mitigated by D5's reporting; the failure names the
  exception type, its message and the message id it happened on.
- **A default timeout of five seconds** → long enough for a scheduler tick, short enough that a
  hung suite is noticed. Every helper takes an explicit `timeout`.

## Migration Plan

Purely additive.

## Open Questions

- Should `wait_for_message` be able to wait for a message matching a filter the *dispatcher*
  would apply, rather than a plain predicate? Attractive, but it would tie the waiting helpers
  to the filter API for a case a lambda already covers.
