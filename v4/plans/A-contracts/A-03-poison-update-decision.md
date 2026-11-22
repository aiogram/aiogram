# A-03 — Decision record: 3.x poison-update boundaries (owner sign-off required)

| Field | Value |
|---|---|
| Status | `done` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (decision recorded in this plan file; no code) |
| Depends on | — |
| Blocks | [3x-01](../3x-quick-wins/3x-01-polling-poison-isolation.md), [3x-02](../3x-quick-wins/3x-02-webhook-poison-200.md) |
| Gate-conditional | no |
| Decisions | D10 (3.x mitigation), D120 ("apply the best-effort policy only once decoding/error/status boundaries are specified"), R13, R27, PD-28, PD-29 |
| Sources | [09 #21–22](../../research/09-3x-quick-wins.md), [10 Layer 2, §5](../../research/10-forward-compatibility.md), [19 R13](../../research/19-review-resolutions.md), [codex-review R27](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D120 and R27: skipping a poison update is **deliberate data loss**. The research says what to do in 3.x ("log, emit
to `errors`, advance the offset"; webhook "log, answer 200"), but not how. In particular, a 3.x `ErrorEvent` requires
an `Update`, and an undecodable update has none. This record fixes the boundaries so 3x-01 and 3x-02 implement a
decision instead of making one. **The owner signs it off before either plan starts.**

## Scope

**In:** the decisions below. Each has a proposed default. The owner confirms or changes it, and the result goes into
*Notes* as "Signed off by owner, <date>".

| # | Question | Proposed default |
|---|---|---|
| Q1 | When does per-update decoding run in polling? | Only when `bot(GetUpdates)` raises `ClientDecodeError`. The fast path is untouched (PD-28) |
| Q2 | What counts as a poison element? | An element of `result` that is a JSON object with an integer `update_id` but fails `Update.model_validate` |
| Q3 | What if an element has no readable `update_id`, or `result` isn't a list? | `GetUpdates(limit=1, offset=<current>)` fallback to isolate it. If one update still yields no id, keep today's backoff and retry (no advance; nothing else can be done safely), log at `ERROR` each time, rate-limited to one line per backoff step |
| Q4 | Offset behaviour | Confirm the poison update (`offset = update_id + 1`) after yielding every good update that precedes it in the batch. Delivery is best-effort, not exactly-once (R13) |
| Q5 | Logging | One `ERROR` on `aiogram.dispatcher` (polling) or `aiogram.webhook` (webhook): `update_id`, the `ValidationError.error_count()` and the first error's `loc` / `type`. **No payload body** at `ERROR`; the body goes to `DEBUG` (ANT-2026-PI9G2NGU) |
| Q6 | `errors` observer | **Yes.** Feed a synthetic `ErrorEvent(update=Update(update_id=<id>), exception=<ValidationError>)` through `dp.errors` with the usual kwargs (`bot`, `dispatcher`, workflow data). `Update` with only `update_id` is valid in 3.x, because every event field is optional. Handlers using `ExceptionTypeFilter(ValidationError)` can catch it; handlers that dereference `event.update.message` get `None`. Document it. Alternative: log only and add no observer call |
| Q7 | Webhook status code | **200 with `{}`** for validation failures on every path (`BaseRequestHandler` inline and background, direct `feed_webhook_update(dict)`), so Telegram stops redelivering. Auth failures keep 401/403/404 |
| Q8 | Webhook `errors` observer | Same as Q6 |
| Q9 | Release type | 3.x **minor** (PD-28), with a changelog section "Undecodable updates are now skipped and reported" |
| Q10 | 4.0 alignment | 3.x Q6 is the precursor of 4.0's `ErrorEvent` with `phase=DECODE` plus `router.unknown_update` (10 Layer 2, D49). 4.0 keeps `ClientDecodeError` with `.raw` (PD-29) |

**Out:**
- The implementation: 3x-01 / 3x-02.
- The 4.0 design: E-14, D-09.

## Checklist

- [ ] Send the table to the owner and record each answer in Notes, verbatim or as "default accepted".
- [ ] If the owner changes Q6/Q8, update the "Scope" bullets of 3x-01 and 3x-02 in the same PR (allowed: plan files
      only).
- [ ] Set `Status: done` only with the sign-off line in Notes.

## Acceptance criteria

- Notes holds "Signed off by owner, <date>" and an answer for each of Q1–Q10.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Always decode per update | Slower happy path | PD-28 |
| Never advance past a poison update | Polling stalls forever | D10 |
| New `TelegramDecodeError` class in 3.x | No new exception classes | PD-29 |

## Validation

Owner sign-off recorded in Notes; links checked (every relative link in this plan and in the plans it names
resolves, using the A-02 link-check script).

## Workflow notes

3x-01 and 3x-02 are blocked until this is `done`. 4.0 plans E-14 and D-09 should read the signed record.

## Notes

Signed off by owner, 2026-11-18 (orchestration session):
- Q1, Q2, Q4, Q5, Q9, Q10: default accepted.
- Q3: default accepted (`limit=1` isolation, then backoff without advancing).
- Q6 / Q8: default accepted (synthetic `ErrorEvent` through `dp.errors`); 3x-01 / 3x-02 scope unchanged.
- Q7: default accepted (200 with `{}` on every path; auth failures keep 401/403/404).
