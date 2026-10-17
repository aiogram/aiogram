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

`aiogram.test.rejections` holds a `Rejection` per text: the description, a `source` naming the Bot
API server, TDLib or the API docs, or `None` for the toolkit's guess, and the code. A
site raises `rejections.NAME(**fields)`. A registry of names rather than an enum or a table
keyed by method, because a text is shared by sites that have nothing else in common, and a
site needs only the name.

A test walks the sources and fails on an `ApiRejection` built from a literal, and the tests'
autouse fixture fails a refusal that was not declared.

### D2. Sourced, not guaranteed

Telegram guarantees no text, so none is a contract, and an earlier list of guaranteed texts
promised more than Telegram does. A description is sourced when it is copied from the Bot API
server's `Client.cpp`, from TDLib or from the MTProto error lists on core.telegram.org, such as
`messages.sendMessage` for `TOPIC_CLOSED` and `TOPIC_DELETED`, and the day the sources were
read is recorded once as `SOURCES_CHECKED`. The fake reproduces sourced texts so that a bot's
heuristic can be tested, not because they are stable. A text that differs from its source by
a word, or has none, is best-effort.

### D3. The code is the contract, so the code is checked

A 429 without `retry_after` would come back as a bare `TelegramAPIError`, and `retry_after`
with another code as a `TelegramRetryAfter`, so `ApiRejection` and `raise_api_error` refuse
both. The other codes `aiogram` maps are left alone. The exception type is observable and the
code is not, as `aiogram.exceptions` carries no `error_code`, so the tests' autouse fixture
records any refusal whose type disagrees with its code and fails the test at teardown, where a
handler's broad `except` cannot hide it.

### D3a. Naming a rejection

The environment remembers, by identity in a weak map, which `ApiRejection` each exception it
raised was made for, so `rejection_of()` and `rejection_fields()` hold when the description
is perturbed. An exception it did not raise is read back against the declared descriptions,
which no two share.

### D3b. Perturbing

`perturb_rejection_descriptions` replaces a description with a marker and its scrambled words,
the same on every run, and leaves the code, the type and `retry_after`. A block declared
without a message is perturbed as well, as the same rejection; a message the test declares is
its own and is left alone.

### D4. Rights for a topic TDLib holds

TDLib refuses a bot lacking `can_manage_topics` or `can_delete_messages` only when it holds the
topic and the bot did not create it (`ForumTopicManager.cpp`, `get_topic_info` and
`is_outgoing`); a topic it does not hold goes on to the server. That includes a topic the bot
deleted, which TDLib drops from its cache, so the creator's exemption goes with the topic.
`_opened_by_bot` keeps that: an unknown or deleted topic skips the check, and the handler
answers `message thread not found` or `TOPIC_DELETED`. An earlier reading, that the rights come
before any lookup, is not what the source does.
