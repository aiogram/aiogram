## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`.

- Refusals were raised as `ApiRejection("...")` with the text inline at about seventy sites,
  and a comment here and there said whether the text was TDLib's or a guess.
- `handle_call` turned an `ApiRejection` into the exception its `error_code` names through
  the session's own response check, so the code and the type already agreed for 400, 403
  and 429.

## Decisions

### D1. One module declares the texts

`aiogram.test.rejections` holds a `Rejection` per text: the wording, an `origin` naming the Bot
API server or TDLib, or `None` for the toolkit's guess, a `guaranteed` flag and the code. A
site raises `rejections.NAME(**fields)`. A registry of names rather than an enum or a table
keyed by method, because a text is shared by sites that have nothing else in common, and a
site needs only the name.

A test walks the sources and fails on an `ApiRejection` built from a literal, and the tests'
autouse fixture fails a refusal that was not declared.

### D2. Guaranteed means sourced and matched by bots

A guaranteed text must cite a source, which `Rejection` enforces, and be one that bots
realistically match on. The list was built from the sources: the Bot API server's
`Client.cpp` for `bot was blocked by the user`, the chat access check, the `message to ...
not found` checks, `message to be replied not found`, `message thread not found`, the expired
query and the flood, and TDLib's parser for `can't parse entities`. A text the code never
cited, such as `TOPIC_CLOSED`, stays best-effort, and so do texts that differ from the server's
by a word.

`message is not modified` is not on the list because the toolkit does not refuse an
unchanged edit.

### D3. The code is the contract, so the code is checked

`ApiRejection` refuses a code other than 400, 403 and 429, since any other would come back as
an exception type the code does not stand for, and a 429 without `retry_after` would come back
as a bare `TelegramAPIError`. `raise_api_error` applies the same rule to `retry_after`. The
exception type is observable and the code is not, as `aiogram.exceptions` carries no
`error_code`, so the tests' autouse fixture checks the type against the code on every refusal
and the tests assert the type. `rejection_of()` reads a caught exception back against the
declared texts, so a test also says which refusal of a code fired, without matching its
wording.

### D4. Rights for a topic TDLib holds

TDLib refuses a bot lacking `can_manage_topics` or `can_delete_messages` only when it holds the
topic and the bot did not create it (`ForumTopicManager.cpp`, `get_topic_info` and
`is_outgoing`); a topic it does not hold goes on to the server. That includes a topic the bot
deleted, which TDLib drops from its cache, so the creator's exemption goes with the topic.
`_opened_by_bot` keeps that: an unknown or deleted topic skips the check, and the handler
answers `message thread not found` or `TOPIC_DELETED`. An earlier reading, that the rights come
before any lookup, is not what the source does.
