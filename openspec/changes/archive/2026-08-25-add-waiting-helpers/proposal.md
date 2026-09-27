## Why

The bot the toolkit was exercised against runs a game engine: `/start_game` returns
immediately, and everything interesting — the night phase beginning, the role cards being
dealt, the vote timer expiring — happens in tasks the trigger never awaited. Every assertion in
the toolkit is an instant snapshot of the world, so a test written against such a bot reads:

```python
await alice.send("/start_game")
assert bot_chat.messages[-1].text.startswith("Night")   # flaky, and usually false
```

The workaround every such test reaches for is the same twenty lines of `asyncio.sleep` in a
loop, re-checking a condition and giving up with `assert False`. Hand-rolled, it is wrong in the
same three ways every time: it overshoots the timeout by up to a full sleep interval, it fails
with a message that says nothing about what the chat actually held, and it dies on the first
service message when the predicate is the natural `lambda m: m.text.startswith(...)` and `text`
is `None`.

That last one is the interesting failure. A chat holds messages of every shape, and a wait has
no business dying on a message it was not asking about — but silently swallowing the exception
turns a genuinely buggy predicate into a plain timeout with no cause.

## What Changes

- **`BotTestEnvironment.wait_for(predicate, ...)`** re-checks any condition until it produces
  something truthy and hands that value back, so it can fetch as well as test. The predicate may
  be synchronous or return an awaitable. A `description=` names the condition in the failure
  message, which for a lambda is otherwise all there is to say.
- **`ChatState.wait_for_message(predicate=None, ...)`** waits for a matching message in one
  chat, matched against **every** message the chat holds — so a message that arrived before the
  call satisfies it immediately and a test never races the send it is waiting for. When several
  match, the newest is returned.
- **`TopicState.wait_for_message(...)`** is the same wait over one topic's own filtered view, so
  a message posted into a sibling topic never satisfies it.
- **A raising predicate counts as "no match"**, not as a failure — and the exceptions are not
  swallowed: a timeout reports what the predicate raised and on which message, so a buggy
  predicate still fails with its real cause.
- **`WaitTimeoutError`**, a `TimeoutError`, is what all three raise. The message names what was
  awaited and enumerates the messages the chat or topic holds instead.
- **The timeout is the promise it reads as**: sleeps are clamped to what is left, so a coarse
  interval gives up on time rather than overshooting.

## Capabilities

### New Capabilities

None — this extends the environment capability rather than adding one.

### Modified Capabilities

- `bot-testing-environment`: gains waiting as stated behavior, for a condition and for a
  message in a chat or topic.

## Impact

- **Code**: a new `aiogram/test/waiting.py` holding the polling core, `wait_for` on the
  environment, `wait_for_message` on `ChatState` and `TopicState`, and `WaitTimeoutError` in
  `aiogram/test/errors.py`. The failure messages reuse a message-describing helper shared with
  the plugin's assertion output.
- **Tests**: a new `tests/test_testing/test_waiting.py`.
- **Docs**: a "Bots with background tasks" section in `docs/dispatcher/testing.rst`.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry.
- **Risk**: a test that waits on a real engine's own `sleep()` is real-time slow, and this
  change deliberately ships no fake clock. Named as a limitation in the documentation rather
  than papered over.
