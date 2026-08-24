## Context

These two clusters are grouped not because they are similar in subject but because they
are identical in structure: each is a piece of state attached to a stored message, a pair
of methods that mutate it, and an update kind whose payload is only truthful if that state
exists. Both are all-or-nothing, and both are the last two exemptions in the completeness
guard introduced by `complete-actor-triggers`. Landing them together is what makes that
guard exemption-free.

`complete-actor-triggers` is a prerequisite: this change reuses its trigger conventions
and edits the exemption set it declares.

The existing world stores `Message` objects directly in `ChatState.messages` and mutates
them through `ChatState.update_message`. Neither piece of state fits inside those objects:

- `Poll.options` carries per-option counts but not *who* voted, so retraction and
  double-voting cannot be computed from it.
- **A `Message` has no reactions field at all.** In the Bot API, reactions exist only as
  update payloads (`MessageReactionUpdated`, `MessageReactionCountUpdated`); there is no
  way to read them back off a message. So reactions must live in the world and be exposed
  through the world, not through the stored message.

Both therefore need a side table keyed by message.

## Goals / Non-Goals

**Goals:**

- Make the design document's own example assertion — "the poll the bot sent is now
  closed" — actually writable.
- Truthful `old_reaction` / `new_reaction` on reaction updates, which is the only reason
  the trigger is worth having.
- Empty the completeness-guard exemption set.

**Non-Goals:**

- **Quiz correctness enforcement.** A vote for the wrong option in a quiz is recorded; the
  fake does not reveal explanations, score anything, or restrict a second attempt.
- Anonymity *enforcement*. An anonymous poll still records which actor voted, because a
  test needs to drive distinct voters; what changes is which update kind is triggerable
  and what the update exposes.
- Reaction permissions (`ChatPermissions.can_send_other_messages`, allowed reaction
  types per chat), consistent with the toolkit's permissions-are-not-enforced stance.
- Paid reactions and their star accounting — part of the deferred stars ledger.

## Decisions

### D1. Votes are the source of truth; counts are derived

`PollState.votes: dict[int, list[int]]` maps a voter's user id to the option indexes they
chose. Option counts are **computed on conversion** to `Poll`, never stored alongside.

This is the change's main hazard and its main decision: an aggregate stored next to its
source drifts the first time a code path updates one and not the other. Deriving is a
handful of lines and cannot drift. The rest of the world model already follows this rule
(`getChatMemberCount` derives from `members`), and this change follows it rather than
becoming the exception.

*Alternative rejected:* incrementing counters on each vote. Faster, and wrong the first
time a retraction is added.

### D2. A poll registry keyed by poll id, referenced from the message

`World.polls: dict[str, PollState]`, with the stored `Message.poll` rebuilt from it on
read. Telegram identifies polls by a string id that appears in `poll_answer` updates
without a chat or message, so the registry is what makes `actor.vote()` resolvable from a
poll id alone — which is exactly how a real handler receives it.

### D3. Reactions are world state, exposed through the world

`ChatState.reactions: dict[message_id, dict[user_id, list[ReactionTypeUnion]]]`, read
through `ChatState.reactions_for(message_id)` and aggregated to a `ReactionCount` list by
`ChatState.reaction_counts(message_id)` — derived on read, by the same rule as D1.

There is deliberately no `Message.reactions`: the Bot API has no such field, and inventing
one would put the fake at odds with the real API in a way a test could come to depend on.
A test asserts through the world (`chat.reactions_for(message_id)`), which is the same
place it already asserts pins and membership.

`old_reaction` for a trigger is read from that table *before* the mutation and
`new_reaction` after, which is the only way those fields can be truthful.

### D4. The bot is a reactor like any other, and the three methods differ

`setMessageReaction` writes into the same per-user table under the bot's user id. This
makes "the bot already reacted" a normal state query rather than a special case, and makes
replace-semantics (a second reaction from the same user replaces the first) fall out of the
data structure instead of needing a rule.

The three reaction methods are *not* variations on one operation, which the names invite
you to assume:

| Method | Scope | Whose |
|---|---|---|
| `setMessageReaction` | one message | the bot's own |
| `deleteMessageReaction` | one message | a named user's (moderation) |
| `deleteAllMessageReactions` | the whole chat | a named user's (moderation) |

`deleteAllMessageReactions` takes no `message_id` at all. Modeling it as "clear this
message" — the natural reading of the name — would be a fidelity claim the fake could not
keep.

### D5. Closed polls reject votes at the trigger, not silently

Voting in a stopped poll raises rather than recording. Telegram simply does not deliver
such an answer; a silent no-op would make a test pass while asserting nothing, which is
the failure mode this whole plan exists to remove. Raising at the trigger — the test's own
code — points at the test rather than at the handler.

### D6. Anonymous polls get the `poll` trigger, non-anonymous get `poll_answer`

Which update a bot receives depends on the poll's anonymity, and modeling that mapping is
what makes a test realistic. Both triggers exist; the environment raises if a test asks for
the one that poll would never produce, naming the reason.

## Risks / Trade-offs

- **Derived aggregates are recomputed on every read (D1, D3)** → marginally more work per
  conversion. Accepted without measurement: these are lists of a handful of entries in a
  test process, and correctness beats a micro-optimization that reintroduces drift.
- **The poll registry is global while messages are per-chat (D2)** → a poll id could
  outlive its message after a delete. Mitigation: deleting a message leaves the poll
  registered but unreferenced, matching Telegram (a deleted poll message does not
  retroactively invalidate the poll id), and a test covers voting after deletion.
- **`Message.poll` is rebuilt on read** → an object identity a test captured earlier is
  stale. Mitigation: the same is already true of every stored message the world mutates,
  and the docs recommend re-reading through the environment rather than holding objects.
- **Reaction update shape is intricate** (`MessageReactionUpdated` vs
  `MessageReactionCountUpdated`, actor vs anonymous) → easy to get subtly wrong.
  Mitigation: scenarios pin `old_reaction`/`new_reaction` explicitly, including the
  removal case, rather than asserting only that a handler fired.
- **Scope creep toward quizzes** → scoring, explanations, one-attempt rules. Mitigation:
  the non-goal is explicit; a quiz test asserts on what the bot does with the answer, which
  is the bot's logic and therefore in scope, not on Telegram's quiz rules.

## Migration Plan

Additive. `sendPoll` returning a stored message rather than a synthesized one may newly
fail a test that asserted an empty chat, the same category of change as
`complete-message-method-modeling`. Land after `complete-actor-triggers`; the final task
is deleting that change's exemption set and watching the completeness guard pass clean.

## Open Questions

- Should `sendPoll` be modeled here or in `complete-message-method-modeling`? It is listed
  here because a poll message without `PollState` is exactly the half-modeled claim this
  change exists to avoid — but if the message change lands first and wants it, the split
  is: message storage there, poll state and everything reading it here.
