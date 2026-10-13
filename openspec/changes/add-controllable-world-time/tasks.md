# Tasks

## 1. The clock

- [ ] 1.1 Give `World` a `now` that starts at `BASE_DATE`, make `next_date()` return it without the per-update tick, and expose it as `env.now` (design D1); verify that feeding several updates produces equal dates, that a forward keeps its origin's date, and update the counter test in `tests/test_testing/test_world.py`
- [ ] 1.2 Add `async BotTestEnvironment.advance_time(seconds | timedelta) -> None` with the due-event queue, one shared route scope, refusal of negative amounts and of overlapping calls, and exception propagation leaving later events queued (design D2); verify with tests for date movement, both refusals leaving the clock unchanged, ordering by moment then scheduling order, an event scheduled mid-advance firing within it, and a raising handler
- [ ] 1.3 Replace `_as_datetime` with `resolve_date(value, now)` handling `timedelta`, `int`, naive and aware `datetime`, and use it for `until_date`, `close_date` and invite-link `expire_date` (design D5); verify each input form, and that invite-link dates are never turned into "forever"
- [ ] 1.4 Add a "Time" section to `docs/dispatcher/testing.rst`: the clock stands still, `advance_time` and its queue, what depends on it, the observed-wording caveat, and how it relates to `looptime` and `time-machine`; verify the docs build shows no new warnings for `testing.rst`

## 2. Restrictions and bans

- [ ] 2.1 Apply `normalize_until` (30 seconds / 366 days means forever) to `until_date` in restrict and ban (design D5); verify both forever edges, a `timedelta` after an advance, and update `test_ban_accepts_a_timestamp` (stored as no end, read as the epoch)
- [ ] 2.2 Settle expired restrictions and bans in `ChatState.member()` through the status helper from `report-restricted-membership-truthfully`, with no update dispatched (design D3, D4); verify through `getChatMember`, `getChatMemberCount`, `chat.member(...)` and an actor's next join, for a present restricted member, an absent one and a banned user, before and after the end
- [ ] 2.3 Document expiring restrictions in the "Time" section; verify the documented example matches a passing test

## 3. Scheduled polls

- [ ] 3.1 Validate `open_period` / `close_date` on `sendPoll` (5 to 2628000 seconds ahead, never both), store the close moment and report it on the poll, and enqueue the close (design D6); verify that out-of-range and combined values raise `TelegramBadRequest` and store nothing, and that the stored poll reports the moment
- [ ] 3.2 Close through the `stopPoll` path on the due moment and dispatch a `poll` update, skipping a poll already stopped; verify the update arrives on reaching the moment and not before, the stored message shows the poll closed, voting afterwards is refused, and a stopped poll produces no update
- [ ] 3.3 Document scheduled closing in the "Time" section, labeling the `poll` update as the toolkit's reading; verify the example matches a passing test

## 4. Live locations

- [ ] 4.1 Reject `editMessageLiveLocation` once `live_period` has elapsed since the message date, after `stopMessageLiveLocation`, or on a location that was never live, except for `0x7FFFFFFF`, with "message can't be edited" (design D3, D8); verify edits within, after, after a stop, on a static location, and on a forever location a year later
- [ ] 4.2 Validate a new `live_period` other than `0x7FFFFFFF`: at most the current one plus 86400, and ending within 90 days of `now`; verify both rejections, an accepted extension, and a switch to forever
- [ ] 4.3 Update the `stopMessageLiveLocation` handler docstring, which says the fake has no clock; verify `make lint` passes

## 5. Message age limits

- [ ] 5.1 Reject `deleteMessage` for a message aged 48 hours or more, and for a dice in a private chat aged 24 hours or less, with "message can't be deleted" (design D8); verify both sides of each boundary
- [ ] 5.2 Make `deleteMessages` skip messages those rules protect; verify a mixed batch removes only the deletable ones and succeeds
- [ ] 5.3 Reject `editMessageText`, `editMessageCaption`, `editMessageMedia` and `editMessageReplyMarkup` on a business message with no `sender_business_bot` and no inline keyboard once more than 48 hours have passed, with "message can't be edited"; verify the rejection for each method, and that a bot-sent business message and one with a keyboard stay editable
- [ ] 5.4 Document the age limits in the "Time" section, labeling batch skipping as the toolkit's reading; verify the docs build

## 6. Answer windows

- [ ] 6.1 Record the issue time with each pending query and fail a pre-checkout answer given more than 10 seconds after issue with the "query is too old" wording (design D7); verify a prompt answer succeeds, an 11-second-late one fails, and a callback query answered an hour later succeeds
- [ ] 6.2 Fail a reply to an incoming ephemeral message given more than 15 seconds after it was sent, in the reply validation from `model-ephemeral-messages` (design D7); verify a prompt `message.reply()` succeeds and a 16-second-late one raises `TelegramBadRequest` and stores nothing
- [ ] 6.3 Document both windows in the "Time" section, with an example of testing a slow handler; verify the example matches a passing test

## 7. Changelog and integration

- [ ] 7.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`, including the observable changes (no per-update tick, `timedelta` from now, the forever rule); verify the fragment renders in the docs build
- [ ] 7.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, the docs build, and `graphify update .`; verify all pass
- [ ] 7.3 Validate the change with `openspec validate add-controllable-world-time --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive add-controllable-world-time`) once its implementation PR into `feature/testing` is merged.
