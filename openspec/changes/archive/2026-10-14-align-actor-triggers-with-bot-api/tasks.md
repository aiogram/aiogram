# Tasks

## 1. Triggers

- [x] 1.1 Re-resolve `click(message=...)` to the stored message in the actor's chat or its ephemeral messages and require the button on it (design D1); verify the stale-copy and missing-button scenarios
- [x] 1.2 Give user edits an `edit_date`, change only passed fields, refuse editing messages the actor did not send (channel posts by the actor's channel excepted); verify each
- [x] 1.3 Name the owner in business connection updates; verify the customer-bound scenario
- [x] 1.4 Add `state` to `update_subscription` (validated) and the expiry date and first-recurring flag to subscription payments; verify each
- [x] 1.5 Set `chat_type` on inline queries and accept `fields=`; verify private and group actors
- [x] 1.6 Validate votes against the poll's options, multiple-answer and revoting rules; verify each refusal and that an allowed revote still works
- [x] 1.7 Give guest messages a unique `guest_query_id`, a `fields=` override and carried-message registration (design D5); verify the canonical handler

## 2. Environment

- [x] 2.1 Stop reporting `SkipHandler` as the handler that ran (design D2); verify the fall-through scenario
- [x] 2.2 Report only unretrieved exceptions in `drain()` (design D3); verify a caught failure and an uncaught one
- [x] 2.3 Treat hand-fed edited messages as replacements (design D4); verify a fed `edited_message`

## 3. Docs, changelog and integration

- [x] 3.1 Update `docs/dispatcher/testing.rst` for each changed trigger; verify the docs build shows no new warnings
- [x] 3.2 Fold the user-visible changes into `CHANGES/1887.feature.rst`
- [x] 3.3 Run `make lint` and `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage; verify both pass
- [x] 3.4 Validate with `openspec validate align-actor-triggers-with-bot-api --strict`

## 4. Review findings

- [x] 4.1 Keep banned users out of membership triggers and join requests, keep an administrator's status on `join()`, and let chat waits take a receiver; verify each with a regression test
