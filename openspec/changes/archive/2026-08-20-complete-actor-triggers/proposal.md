## Why

The toolkit's whole premise is that a test triggers a real event and the real dispatcher
routes it. But **15 of the 26 `Update` variants have no trigger at all**: `channel_post`,
`edited_channel_post`, `guest_message`, `message_reaction`, `message_reaction_count`,
`chosen_inline_result`, `shipping_query`, `pre_checkout_query`, `purchased_paid_media`,
`poll`, `poll_answer`, `chat_join_request`, `chat_boost`, `removed_chat_boost`,
`managed_bot` and `subscription`. A handler registered for any of them cannot be reached
except by hand-assembling an `Update` and calling a private helper — exactly the
scaffolding the toolkit exists to delete.

This is the larger half of the gap, and it is the half that makes several outbound method
clusters pointless. `answerShippingQuery` and `answerPreCheckoutQuery` cannot be exercised
without a query to answer. `approveChatJoinRequest` cannot be exercised without a request
to approve. Modeling those methods without their triggers buys nothing.

There is also a concrete defect here. `handle_answer_callback_query` is `return True` —
there is no registry of outstanding queries, so answering a stale, already-answered or
entirely fabricated `callback_query.id` silently succeeds. `answerInlineQuery` is the
same. Both hide a real production failure ("query is too old and response timeout expired")
behind a green test.

## What Changes

- **Triggers for the missing update kinds**, each producing an update indistinguishable in
  shape from Telegram's:
  - Channel posts: `channel_post` and `edited_channel_post`, against a channel chat.
  - Queries: `chosen_inline_result`, `shipping_query`, `pre_checkout_query`.
  - Membership and access: `chat_join_request`, `chat_boost`, `removed_chat_boost`.
  - Payments: `purchased_paid_media`, and a `successful_payment` message closing the flow.
  - Remaining kinds — `guest_message`, `managed_bot`, `subscription` — get triggers of the
    same shape so no update kind is unreachable.
  - `poll`, `poll_answer` and `message_reaction` are triggered by
    `model-polls-and-reactions`, which owns the state they read.
- **A pending-query registry.** Every trigger that produces a query registers its id.
  `AnswerCallbackQuery`, `AnswerInlineQuery`, `AnswerShippingQuery` and
  `AnswerPreCheckoutQuery` validate against it and raise `TelegramBadRequest` for an
  unknown or already-answered id — closing the defect above.
- **Join requests become world state.** `ChatState.join_requests` holds pending requests;
  `ApproveChatJoinRequest` makes the requester a member and `DeclineChatJoinRequest`
  clears the request without doing so, both failing on a request that does not exist.
- **The payment flow is end-to-end testable.** A test drives `shipping_query` →
  `pre_checkout_query` → a message carrying `successful_payment`, with the bot's answers
  validated against the registry at each step.
- **Channel chats are first-class.** A blueprint can declare a channel, and posts to it
  route as `channel_post` rather than `message`.

**BREAKING for tests that answer fabricated query ids**: a test that calls
`answer_callback_query` with an id it invented, or answers the same query twice, now
raises `TelegramBadRequest`. That is the defect being fixed, and it is the one behavior
change in this proposal.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the supported trigger set is extended to every `Update`
  variant, a pending-query registry is added with validation on the four answer methods,
  join requests become world state, and channel chats gain their own routing.
- `bot-testing-pytest`: the per-test isolation guarantee is extended to cover the new
  mutable state — pending join requests and outstanding queries — so an unanswered query
  in one test cannot be answered from another.

## Impact

- **Code**: `aiogram/test/actors.py` (the triggers — the bulk of the change),
  `world.py` (pending queries, join requests, channel chats), `blueprint.py` (declaring
  channels and pending join requests), `modeling.py` (the four answer methods and the two
  join-request methods). The plugin needs no new fixtures — the triggers are actor methods
  reachable from the existing environment fixture.
- **Tests**: a substantial new suite under `tests/test_testing/`, holding the package at
  100%. A guard test asserting that *every* `Update` field has a trigger is the backstop
  that keeps this complete as the Bot API grows.
- **Docs**: a "Triggering every update kind" section in `docs/dispatcher/testing.rst`,
  plus a payments walkthrough.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`, calling out the query-validation
  behavior change explicitly.
- **Compatibility**: no new dependencies; Python 3.10–3.14 and PyPy 3.11 as before.
- **Risk**: this is the largest change in the plan and the one most likely to want
  splitting — the proposal is written so queries/join-requests/channel-posts and
  payments/boosts can land as two PRs against the same spec if the diff grows unwieldy.
