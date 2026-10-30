## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. Each finding came from a reproduced audit of the
actor triggers and the environment. This document records only the choices the fixes make.

## Goals / Non-Goals

**Goals:**

- A trigger produces only updates Telegram would deliver, and refuses the rest as a setup
  error, as the closed-poll vote already does.

**Non-Goals:**

- Inline query `chat_type` for chats the actor is not bound to: the actor's binding is the
  only signal.

## Decisions

### D1. Explicit click targets are re-resolved

`click(message=m)` looks `m` up by id in the actor's chat, or among its ephemeral messages.
It requires the button on the stored version, which is the one dispatched. This reuses the
visibility check the ephemeral change added.

### D2. A skip is not a handler error

`_HandlerMiddleware` catches `SkipHandler`, clears the record's handler, module and router,
and re-raises without recording an exception. `CancelHandler` is not caught: aiogram's
handler loop catches only `SkipHandler`, so a `CancelHandler` raised by a handler fails the
update, and the route keeps naming that handler, with the exception.

### D3. Retrieved exceptions are recognized through asyncio's own flag

A finished task whose exception was retrieved has `_log_traceback` cleared by asyncio. The
drain reads it with `getattr(task, "_log_traceback", True)`, so on an implementation
without the attribute it keeps reporting, as today.

### D4. Edits by hand-fed updates replace the stored message

`_register_carried_message` treats `edited_message`, `edited_channel_post` and
`edited_business_message` as replacements through `chat.update_message`, rather than as new
messages that collide.

### D5. Guest query ids come from the query counter; answering stays record-only

The id is allocated with `world.next_query_id()` without a kind, so it is unique but not
tracked as outstanding. `answerGuestQuery` stays on the record-only list with the other
mini-app handoffs: the recorded call is still the whole useful assertion.

## Risks / Trade-offs

- [Tests that relied on clicking a non-existent button, editing the bot's messages as a
  user, or invalid votes now fail] → each was a test passing on an update Telegram would not
  send; the failure names the rule.
