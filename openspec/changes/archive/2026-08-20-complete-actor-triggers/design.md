## Context

`UserActor` currently exposes `send`, `edit`, `click`, `inline_query`, `join`, `leave`,
the business triggers and the community triggers. Each builds an `Update` and awaits
`dispatcher.feed_update(bot, update, **kwargs)` through the private `_feed` helper. The
shape is proven; what is missing is coverage.

Two structural facts shape this change:

1. **`Update` is generated.** Its variants come from `.butcher`, so a Bot API bump can add
   one. A hand-maintained list of triggers will silently fall behind unless something in
   aiogram's own CI compares the two.
2. **Queries are ephemeral in Telegram and permanent in the fake.** `World.next_query_id()`
   hands out ids and forgets them. Every answer method therefore succeeds unconditionally,
   which is how the `answerCallbackQuery` defect got in.

## Goals / Non-Goals

**Goals:**

- No registered handler is unreachable from a test. That is the whole point.
- Answering a query is validated, so the "query is too old" failure class is testable.
- Join requests and the payment flow work end to end, since their methods are useless
  without their triggers.
- Completeness stays true as the Bot API grows, enforced by a test rather than by
  diligence.

**Non-Goals:**

- Modeling *why* an update would arrive. A `chat_boost` trigger produces the update; it
  does not model boost counts, levels, or a boost economy. Same for `subscription` and
  `managed_bot`: the trigger exists so the handler runs.
- Query expiry by time. Validation is "outstanding or not", never "older than 60 seconds".
  There is no clock to expire against, and a time-based fake would be flakiness, not
  fidelity.
- Enforcing the *order* of a payment flow. A test may trigger a pre-checkout query without
  a preceding shipping query, because real bots with digital goods do exactly that.
- The webhook HTTP layer and the polling loop, which remain out of scope for the toolkit.

## Decisions

### D1. A completeness guard test, not a hand-checked list

A parametrized test walks `Update`'s model fields and asserts each one has a registered
trigger. A new Bot API variant fails aiogram's CI with the variant named, which is how the
synthesis guard already protects the outbound side. This is the single most important
decision in the change: it converts "we covered everything today" into an invariant.

Variants owned by another change (`poll`, `poll_answer`, `message_reaction`,
`message_reaction_count`) are listed in an explicit, named exemption set that
`model-polls-and-reactions` empties. An exemption set that is visible and shrinking beats
a list that is invisible and forgotten.

### D2. Pending-query registry on the world

`World.pending_queries: dict[str, QueryKind]`. A trigger that issues a query registers its
id; the answer handler pops it, raising `TelegramBadRequest` when absent with Telegram's
own wording ("query is too old and response timeout expired or query ID is invalid").

Popping — rather than marking answered — makes double-answer and unknown-id the same code
path, which is also what Telegram reports.

*Alternative rejected:* validating inside `CallbackQuery` construction or in the session.
The registry belongs to the world because it is state with a lifetime, and the world is
what `Blueprint.build()` already isolates per test.

*Consequence:* this is the change's one breaking behavior. A test that answers a fabricated
id starts failing. That is the defect, and the changelog says so plainly.

### D3. Channel posts route by chat type, not by a separate trigger

`actor.send(...)` in a chat whose `type` is `channel` produces `channel_post` instead of
`message`, and editing a stored channel post produces `edited_channel_post`. Reusing the
existing trigger keeps the actor API small and matches how the framework itself decides:
by the chat the event belongs to.

Because a channel post has no `from_user` in the ordinary sense, the actor is used to
resolve the *author signature* path rather than being forced into `from_user`.

### D4. Join requests are state, boosts are not

`ChatState.join_requests: dict[int, JoinRequestState]` holds the pending request, because
approving one has an observable consequence — the requester becomes a member — that a test
would assert. `chat_boost` has no such consequence in a fake with no boost model, so its
trigger produces the update and stores nothing.

The line is the one the design doc already draws: state exists when an assertion needs it.

### D5. Payment triggers are independent steps, not a scripted flow

`actor.shipping_query(...)`, `actor.pre_checkout_query(...)` and `actor.pay(...)` (which
appends a `successful_payment` message) are separate triggers a test composes. No trigger
requires a predecessor.

*Alternative rejected:* a single `actor.complete_payment()` that drives all three. It would
hide precisely the intermediate states a payment test needs to assert on, and it would
force an ordering real bots do not always follow.

### D6. Trigger signatures follow the existing actors, not the Bot API

Each trigger takes the few arguments a test would vary and fills the rest from the actor's
binding and the world, exactly as `send`/`click` already do. `**data` is forwarded to
`feed_update` on every trigger so contextual dependency injection keeps working
uniformly.

## Risks / Trade-offs

- **Query validation breaks existing tests (D2)** → any test answering an invented id now
  fails. Mitigation: it is the defect being fixed; the changelog calls it out as a behavior
  change, and the failure message names the fix (trigger the query, or override the method).
- **The change is large** → review burden, and a long-lived branch. Mitigation: the spec is
  written so it can land as two PRs — queries + join requests + channel posts, then
  payments + boosts + the remaining kinds — with the completeness guard turned on only at
  the end of the second.
- **Triggers for kinds nobody uses (`managed_bot`, `subscription`, `guest_message`)** →
  effort spent on cold paths. Accepted: they are a handful of lines each, and the
  alternative is an incomplete guard, which defeats D1.
- **Fabricating a plausible `chat_boost` or `subscription` payload** → the update may be
  schema-valid but semantically odd. Mitigation: reuse `synthesize` seeded from the world
  for the parts a test does not specify, which is the same trade-off the outbound side
  already accepts.
- **Channel author signatures (D3)** → getting `from_user`/`sender_chat`/`author_signature`
  wrong would make channel tests subtly unrealistic. Mitigation: scenarios asserting the
  shape, and the `message` handler *not* firing for a channel post.

## Migration Plan

Additive apart from D2. Rollout:

1. Land the registry and the query validation with the triggers that feed it, so the
   breaking behavior arrives together with the means to satisfy it.
2. Land the remaining triggers and enable the completeness guard.
3. `model-polls-and-reactions` empties the exemption set.

Rollback is removing the validation from the four answer handlers; the triggers themselves
are purely additive.

## Open Questions

- Should an unanswered outstanding query fail the test at environment teardown, the way a
  real bot would leave a user with a spinning button? Tempting, and genuinely diagnostic,
  but it would fail existing green suites for a warning-level problem. Deferred; a
  `env.calls`-style assertion helper is the lighter first step.
