## Context

The toolkit's error story was built around one good idea: a call the fake refuses should fail
the way it fails in production, through `BaseSession.check_response`, so the exception type, its
message and the error pipeline under test are the real ones rather than a lookalike. That is
still right.

What was missing is that not every refusal is a refusal *by Telegram*. Some are the fake saying
"you did not tell me about this", and dressing those up as a Bad Request hands the test's own
setup bug to the bot under test, which is the one consumer guaranteed to hide it.

The failure is silent by construction: a bot with an `except TelegramBadRequest` is a
well-written bot, and the better its error handling, the more thoroughly it swallows the message
that would have explained the problem.

## Goals / Non-Goals

**Goals:**

- A modeled rejection stays testable: `pytest.raises(TelegramBadRequest, match=...)` against
  Telegram's own wording.
- A setup gap fails the test, loudly, with a message that says what to declare.
- The boundary is stated where the next handler is written, not only in the changelog.

**Non-Goals:**

- A general error taxonomy. Two types, one rule each, because the question a raise site has to
  answer is binary: *would Telegram answer this?*
- Catching the setup type anywhere. `WorldLookupError` is not converted, not wrapped, and not
  handled by the toolkit at any layer — that is the entire point.
- Changing what any *modeled* method rejects. Only the type carrying the refusal moved.

## Decisions

### D1. Two types, and the rule is "would Telegram answer this?"

`ApiRejection` means yes: forwarding a message that does not exist, demoting the chat owner,
closing a closed poll, answering a query twice. Bot code legitimately catches those, and a test
of that `except` branch is a real test. `handle_call` catches it and calls `env.fail`, which
routes through `check_response` and produces the genuine `TelegramBadRequest`.

`WorldLookupError` means no: the blueprint never declared this user, chat, sticker set, poll,
gift or business connection; the environment never recorded this charge; the gift id is not in
the fake's catalogue; the method addresses an inline message, which the toolkit does not model.
Nothing converts it.

The rule is deliberately a question about *Telegram*, not about severity or about which layer
noticed. "Chat not found" is an `ApiRejection` even though it usually means the blueprint is
missing a chat — because a bot really can call `getChat` on an id that does not exist, and
Telegram really does answer that with a Bad Request. `world.chat(...)`, reached when the *test*
asks the world for a chat, is a `WorldLookupError`. Same words, different question.

### D2. `ApiRejection` carries Telegram's wording, without the prefix

The message is what Telegram sends, minus the `Bad Request:` prefix that `handle_call` adds when
converting — so a test can `match=` on the string a real bot would see, and the same exception
raised outside a call is not carrying a prefix that would then be doubled.

### D3. `ApiRejection` is public, because the world is reachable without a call

A test that reaches into the world directly — `chat.require_message(999)`, `chat.topic(999)`,
`chat.invite_link(url)` — is outside any call, so there is no `handle_call` to convert the
refusal. Those raise `ApiRejection` as it is, and a test that wants to assert on them needs the
name, so it is exported from `aiogram.test` alongside `WorldLookupError`.

*Alternative rejected:* making the world's own accessors raise a third, "outside a call" type.
It is the same refusal for the same reason; only the audience differs.

### D4. The boundary is documented in `modeling.py`'s module docstring

The decision a handler author faces is which type to raise, and they face it while writing a
handler. The module docstring states both rules there, next to the copy-boundary rule, so the
answer is in view at the moment the question arises rather than in a changelog entry.

### D5. Where a refusal lives decides nothing; what it means decides everything

Both types are raised from both `world.py` and `modeling.py`. `ChatState.require_message` raises
`ApiRejection`, because a bot editing a message it already deleted is a Bad Request; a few
definitions further down the same file, `World.chat` raises `WorldLookupError`, because a chat
the blueprint never declared is a setup gap.

Sorting by module would have been mechanical and wrong, and it is worth saying so: the layer a
check sits in has nothing to do with whether Telegram would answer it.

## Risks / Trade-offs

- **A raise site sorted the wrong way** → in the `ApiRejection` direction it reintroduces the
  silent swallow. Mitigated by the rule being a single concrete question, by the world's
  lookups staying loud by default, and by every re-pointed test asserting the type explicitly.
- **A user catching `WorldLookupError` on purpose** → possible, and it defeats the design. It is
  a `LookupError`, so a bare `except Exception` in the bot under test would also catch it —
  nothing can prevent that, and the documentation says what the type is for.
- **Two names to learn** → mitigated by the failure messages themselves: a `WorldLookupError`
  says what to declare, which is the whole reason it is worth a second type.

## Migration Plan

Behavioral, and deliberately so: calls that used to fail with `TelegramBadRequest` for an
undeclared entity now raise `WorldLookupError` instead. A suite that was passing while
swallowing a setup gap will start failing — which is the change working.

## Open Questions

- Should `NoFileContentError` — the download-with-no-content error — be folded into
  `WorldLookupError`? It is already a `LookupError` with the same "here is what to declare"
  shape, but its dedicated type carries the `file_id` as an attribute, so it stays separate for
  now.
