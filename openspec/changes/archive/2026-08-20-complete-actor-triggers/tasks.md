## 1. Pending-query registry (ship first — it closes a defect)

- [x] 1.1 Add `World.pending_queries` and register ids from `click()` and `inline_query()` (design D2)
- [x] 1.2 Make `AnswerCallbackQuery` and `AnswerInlineQuery` pop the id, raising `TelegramBadRequest` with Telegram's wording when absent
- [x] 1.3 Regression test: answering a fabricated callback query id fails — the case that currently returns `True`
- [x] 1.4 Regression test: answering the same query twice fails; answering the query being handled succeeds
- [x] 1.5 Test: outstanding queries do not leak between environments built from one blueprint

## 2. Chat join requests

- [x] 2.1 Add `ChatState.join_requests` (a blueprint declaration was not needed — the trigger records the request)
- [x] 2.2 Add an actor trigger producing `chat_join_request` and recording the request
- [x] 2.3 Model `ApproveChatJoinRequest` (adds the member, clears the request) and `DeclineChatJoinRequest` (clears only)
- [x] 2.4 Raise `TelegramBadRequest` when no such request is pending
- [x] 2.5 Tests: approve adds the member, decline does not, acting on a non-existent request fails, declared requests reach handlers

## 3. Channel posts

- [x] 3.1 Route `actor.send()` in a channel chat to `channel_post`, and edits to `edited_channel_post` (design D3)
- [x] 3.2 Attribute a channel post to the channel: no `from_user`, `sender_chat` set, `author_signature` from the actor
- [x] 3.3 Tests: a `channel_post` handler receives the post and a `message` handler does not; editing produces `edited_channel_post`; the post is stored in the chat

## 4. Query triggers

- [x] 4.1 Add `chosen_inline_result`, `shipping_query` and `pre_checkout_query` triggers, registering query ids where applicable
- [x] 4.2 Make `AnswerShippingQuery` and `AnswerPreCheckoutQuery` validate against the registry
- [x] 4.3 Tests: each update reaches its handler, `event_from_user` resolves, and answering an unregistered id fails

## 5. Payments end to end

- [x] 5.1 Add a trigger appending a message carrying `successful_payment` (design D5)
- [x] 5.2 Add a `purchased_paid_media` trigger
- [x] 5.3 Test: shipping query → answer → pre-checkout query → answer → payment reaches the `successful_payment` handler
- [x] 5.4 Test: answering pre-checkout with `ok=False` clears the query and produces no payment message
- [x] 5.5 Test: a pre-checkout query without a preceding shipping query works (digital goods path)

## 6. Remaining update kinds

- [x] 6.1 Add `chat_boost` and `removed_chat_boost` triggers, storing nothing (design D4)
- [x] 6.2 Add `guest_message`, `managed_bot` and `subscription` triggers
- [x] 6.3 Seed unspecified payload parts from the world through `synthesize`
- [x] 6.4 Tests: each update kind reaches a handler registered for it

## 7. Completeness guard

- [x] 7.1 Add a parametrized test walking `Update`'s model fields that **invokes** each trigger and asserts the update carries that field — checking a method merely exists would pass vacuously (design D1)
- [x] 7.1b Add `add_bot()` / `remove_bot()` so `my_chat_member` has a real trigger, which the guard above exposed as missing
- [x] 7.2 Declare the named exemption set for the variants owned by `model-polls-and-reactions`, with a comment naming that change
- [x] 7.3 Verify the guard fails with the variant named when a trigger is removed

## 8. Documentation

- [x] 8.1 Add a "Triggering every update kind" section to `docs/dispatcher/testing.rst`
- [x] 8.2 Add a payments walkthrough covering the full shipping → pre-checkout → payment flow
- [x] 8.3 Document query validation, including the failure message and how to satisfy it
- [x] 8.4 Build docs and fix any new warnings

## 9. Release readiness

- [x] 9.1 `CHANGES/<issue-or-pr>.feature.rst`, calling out query validation explicitly as a behavior change
- [x] 9.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 9.3 Confirm the parametrized synthesis guard over every generated return type still passes
- [x] 9.4 Verify the new suite runs without `--redis` / `--mongo` and stays inside the Python 3.10 floor
