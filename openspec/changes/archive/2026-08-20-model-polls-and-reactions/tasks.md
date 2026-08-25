## 1. Poll state

- [x] 1.1 Add `PollState` and `World.polls` keyed by poll id (design D2)
- [x] 1.2 Store votes as voter id → chosen option indexes; derive option counts on conversion, never store them (design D1)
- [x] 1.3 Add conversion from `PollState` to `Poll`, rebuilding `Message.poll` on read
- [~] 1.4 Blueprint declaration for a poll — **skipped**: `sendPoll` is the only way a poll enters the world, and a declaration would be a second construction path for no assertion a test cannot already write
- [x] 1.5 Tests: counts always equal the recorded voters, including after a retraction; environments stay isolated

## 2. Poll methods

- [x] 2.1 Model `SendPoll` to store the poll and append the carrying message (the open question resolved itself: `complete-message-method-modeling` shipped without it)
- [x] 2.2 Model `StopPoll` to close the stored poll and return it with final counts
- [x] 2.3 Raise `TelegramBadRequest` when the target is unknown, carries no poll, or is already closed
- [x] 2.4 Tests: send → vote → stop returns the stored poll with the votes; all three error paths

## 3. Poll triggers

- [x] 3.1 Add `actor.vote(...)` producing `poll_answer` and recording the vote
- [x] 3.2 Support retracting a vote where Telegram supports it
- [x] 3.3 Add `poll_update()` for the anonymous aggregate form, and raise from `vote()` on an anonymous poll, naming the reason (design D6)
- [x] 3.4 Raise on voting in a closed poll (design D5)
- [x] 3.5 Tests: a vote reaches the handler and the stored poll; retraction; closed-poll rejection; voting after the carrying message was deleted

## 4. Reaction state

- [x] 4.1 Store reactions per message as user id → reaction types (design D3)
- [x] 4.2 Derive reaction counts on read through `ChatState.reaction_counts` — there is no `Message.reactions` field in the Bot API (design D3)
- [~] 4.3 Blueprint declaration for reactions — **skipped**: `ChatState.set_reaction` already lets a test seed them in one line, which the suite uses
- [x] 4.4 Tests: derived counts match the recorded reactors; a message with no reactions has no counts

## 5. Reaction methods

- [x] 5.1 Model `SetMessageReaction` writing under the bot's user id (design D4)
- [x] 5.2 Model `DeleteMessageReaction` (one actor, one message) and `DeleteAllMessageReactions` (one actor, chat-wide — it takes no `message_id`)
- [x] 5.3 Raise `TelegramBadRequest` for an unknown or deleted message
- [x] 5.4 Tests: bot reacts; a second reaction replaces the first; clearing empties; error path

## 6. Reaction triggers

- [x] 6.1 Add `actor.react(...)` producing `message_reaction`, reading `old_reaction` before the mutation and `new_reaction` after
- [x] 6.2 Support removing a reaction, producing an empty `new_reaction`
- [x] 6.3 Add the `message_reaction_count` trigger for the anonymous aggregate form
- [x] 6.4 Tests: changing a reaction reports the previous emoji; removal; the aggregate form reaches its handler

## 7. Completeness guard

- [x] 7.1 Delete the exemption set declared by `complete-actor-triggers`
- [x] 7.2 Verify the guard passes with every `Update` variant covered and no exemptions

## 8. Documentation

- [x] 8.1 Add a "Polls and quizzes" section to `docs/dispatcher/testing.rst`
- [x] 8.2 Add a "Reactions" section
- [x] 8.3 State the non-goals plainly: no quiz scoring, no anonymity or reaction-permission enforcement, no paid reactions
- [x] 8.4 Build docs and fix any new warnings

## 9. Release readiness

- [x] 9.1 `CHANGES/<issue-or-pr>.feature.rst`, noting that `sendPoll` now stores its message
- [x] 9.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 9.3 Confirm the parametrized synthesis guard over every generated return type still passes
