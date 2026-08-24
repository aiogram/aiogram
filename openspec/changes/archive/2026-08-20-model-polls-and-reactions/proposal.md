## Why

"The poll the bot sent is now closed" is the example assertion the toolkit's own design
document uses to explain what a world model is for — and it is currently unwritable.
`sendPoll` returns a synthesized `Message` that is never stored, `stopPoll` returns a
synthesized `Poll` unrelated to it, and there is no `poll` or `poll_answer` trigger, so a
poll-answer handler cannot be reached at all. A quiz bot — one of the most common bot
shapes there is — has no test path.

Reactions are in the same position. `setMessageReaction`, `deleteMessageReaction` and
`deleteAllMessageReactions` are recorded and discarded, stored messages carry no
reactions, and there is no `message_reaction` or `message_reaction_count` trigger. A bot
that reacts to a message and a bot that responds to being reacted to are both untestable.

Both clusters are all-or-nothing. A modeled `stopPoll` without a stored poll is a fidelity
claim the fake cannot keep; a `message_reaction` trigger without stored reactions produces
an update whose `old_reaction` is fiction. They ship together because they are the two
remaining update kinds exempted from the completeness guard that `complete-actor-triggers`
introduces — this change is what empties that exemption set.

## What Changes

- **`PollState` in the world.** A poll carries its id, question, options, type, anonymity,
  multiple-answer flag, correct option and explanation for quizzes, per-option vote counts,
  the voters who chose what, and whether it is closed.
- **`SendPoll` stores a real poll** on a real message, and `StopPoll` closes *that* poll,
  returning it with its final vote counts. Stopping an unknown, non-poll or already-closed
  message fails with `TelegramBadRequest`.
- **Voting is an actor trigger.** `actor.vote(...)` produces a `poll_answer` update,
  records the vote against the stored poll, and updates the counts; retracting a vote is
  supported for non-anonymous polls, as Telegram allows.
- **A `poll` update trigger** for the anonymous case, where a bot sees aggregate state
  rather than individual answers.
- **Reactions become message state.** A stored message carries its reactions per user;
  `SetMessageReaction`, `DeleteMessageReaction` and `DeleteAllMessageReactions` are applied
  to it.
- **Reaction triggers.** `actor.react(...)` produces a `message_reaction` update with
  truthful `old_reaction` and `new_reaction` derived from stored state, and
  `message_reaction_count` for the anonymous aggregate form.
- **The completeness guard's exemption set is emptied**, so every `Update` variant has a
  trigger with no exceptions.

No breaking changes. Tests asserting on `env.calls` keep passing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: polls and message reactions become world state with their
  methods modeled and their update kinds triggerable, and the requirement that every
  `Update` variant is reachable loses its exemptions.

## Impact

- **Code**: `aiogram/test/world.py` (`PollState`, reactions on stored messages),
  `blueprint.py` (declaring a poll or existing reactions), `actors.py` (the vote and react
  triggers), `modeling.py` (`SendPoll`, `StopPoll`, the three reaction methods).
- **Tests**: a new module under `tests/test_testing/`, holding the package at 100%.
- **Docs**: "Polls and quizzes" and "Reactions" sections in `docs/dispatcher/testing.rst`.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Dependency**: this change assumes `complete-actor-triggers` has landed, since it
  empties that change's exemption set and reuses its trigger conventions.
- **Compatibility**: no new dependencies; Python 3.10–3.14 and PyPy 3.11 as before.
- **Risk**: moderate. Poll vote accounting is the first place the fake maintains a derived
  aggregate (counts alongside voters), which is a class of bug the rest of the world model
  has avoided by storing one source of truth. The design addresses this directly.
