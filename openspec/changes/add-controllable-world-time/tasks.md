# Tasks

## 1. The clock

- [ ] 1.1 Give `World` a `now` that starts at `BASE_DATE`, make `next_date()` return it without the per-update tick, and expose it as `env.now` (design D1); verify that feeding several updates produces equal dates, and update the counter test in `tests/test_testing/test_world.py`
- [ ] 1.2 Add `async BotTestEnvironment.advance_time(seconds | timedelta)` with a due-event queue ordered by moment then scheduling order, moving `now` to each event's moment before dispatching it, and refusing a negative amount (design D2); verify with tests for date movement, refusal leaving the clock unchanged, and event ordering
- [ ] 1.3 Add a "Time" section to `docs/dispatcher/testing.rst`: the clock stands still, `advance_time`, what depends on it, and that the bot's own wall-clock reads are out of scope; verify the docs build shows no new warnings for `testing.rst`

## 2. Restrictions and bans

- [ ] 2.1 Resolve `until_date` against `now`, apply the 30-second / 366-day forever rule, store forever as `None`, report it as `0`, and treat a basic-group ban as forever (design D5); verify with tests for a `timedelta` after an advance, both forever edges, and the reported `0`
- [ ] 2.2 Make membership reads time-aware: a restricted member past `until_date` reads as `member`, a banned user as `left`, the stored state unchanged and no update dispatched (design D3, D4); verify with tests through `getChatMember` and `chat.member(...)` before and after an advance
- [ ] 2.3 Document expiring restrictions in the "Time" section; verify the documented example matches a passing test

## 3. Scheduled polls

- [ ] 3.1 Validate and store `open_period` / `close_date` on `sendPoll` (5 to 2628000 seconds ahead) and schedule the close (design D2); verify that out-of-range values raise `TelegramBadRequest` and store nothing
- [ ] 3.2 On the due moment, close the poll and dispatch a `poll` update with the closed poll; verify with tests that the update arrives on reaching the moment and not before, that voting afterwards is refused, and that a poll already stopped by `stopPoll` produces no second update
- [ ] 3.3 Document scheduled closing in the "Time" section, including that the `poll` update is the toolkit's reading of the Bot API; verify the example matches a passing test

## 4. Live locations

- [ ] 4.1 Reject `editMessageLiveLocation` once `live_period` has elapsed since the message date, except `0x7FFFFFFF`, with "message can't be edited" (design D3, D6); verify edits within, after and for a forever location
- [ ] 4.2 Validate a new `live_period`: at most the current one plus 86400, and ending within 90 days of `now`; verify both rejections and an accepted extension
- [ ] 4.3 Update the `stopMessageLiveLocation` handler docstring, which says the fake has no clock; verify `make lint` passes

## 5. Message age limits

- [ ] 5.1 Reject `deleteMessage` for a message aged 48 hours or more, and for a dice in a private chat aged 24 hours or less, with "message can't be deleted" (design D6); verify with tests at both sides of each boundary
- [ ] 5.2 Make `deleteMessages` skip messages those rules protect; verify a mixed batch removes only the deletable ones and succeeds
- [ ] 5.3 Reject editing a business message the bot did not send and that has no inline keyboard once more than 48 hours have passed, with "message can't be edited"; verify the rejection, and that a bot-sent business message and one with a keyboard stay editable
- [ ] 5.4 Document the age limits in the "Time" section; verify the docs build

## 6. Answer windows

- [ ] 6.1 Record the issue time with each pending query and fail a pre-checkout answer given more than 10 seconds after issue with the existing "query is too old" wording (design D7); verify a prompt answer succeeds, an 11-second-late one fails, and other query kinds are unaffected by time
- [ ] 6.2 Fail a reply to an incoming ephemeral message given more than 15 seconds after it was sent (requires `model-ephemeral-messages`); verify a prompt `message.reply()` succeeds and a 16-second-late one raises `TelegramBadRequest` and stores nothing
- [ ] 6.3 Document both windows in the "Time" section, with an example of testing a slow handler; verify the example matches a passing test

## 7. Changelog and integration

- [ ] 7.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`, including the three observable changes (no per-update tick, forever as `0`, `timedelta` from now); verify the fragment renders in the docs build
- [ ] 7.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, and the docs build; verify all pass
- [ ] 7.3 Validate the change with `openspec validate add-controllable-world-time --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive add-controllable-world-time`) once its implementation PR into `feature/testing` is merged.
