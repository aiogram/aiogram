# 3x-23 — Mutation warnings and Bot API ledger-field warnings

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [3x-20](3x-20-deprecation-machinery.md), [A-11](../A-contracts/A-11-migration-registry.md), [A-05](../A-contracts/A-05-bench-harness.md), [C-26](../C-butcher/C-26-removal-inventory-signature-table.md) |
| Blocks | [3x-24](3x-24-migration-baseline-release.md) |
| Gate-conditional | no |
| Decisions | D15, D6 (4.0 ledger reset, explicit exception to D71), D72 (`AiogramApiDeprecationWarning`), D74, R28, PD-13 |
| Sources | [16 §2](../../research/16-support-policy.md), [11 §1](../../research/11-removals.md), [02 §4](../../research/02-butcher.md), [README breaking changes 2, 8](../../research/README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Two kinds of 4.0 removal can only be seen when user code touches an object:

1. **Mutation (D15).** All types become immutable. The 16 `MutableTelegramObject` bases in `aiogram/types/` and
   their subclasses (keyboards and buttons, `InputMedia*`, `InputMessageContent`, `InlineQueryResult*`,
   `MessageEntity`, `BotCommand`, `ChatPermissions`, `LabeledPrice`, `MenuButton*`, `PassportElementError*`,
   `ForceReply`, `ReplyKeyboardRemove`, `KeyboardButtonPollType`, …) accept attribute writes today.
2. **The ledger reset (02 §4, README breaking change 8).** Every Bot API field and entity deprecated during 3.x is
   dropped in 4.0: 122 fields in 35 files (`reply_to_message_id` ×18, `allow_sending_without_reply` ×18,
   `receiver_user_id`, `callback_query_id`, the 35 7.3-era `Chat` fields, `switch_pm_*`, …), plus the types
   `KeyboardButtonRequestUser`, `UserShared` and `StoryAreaPosition`. Also the legacy reply parameters in the
   hand-written `Message.send_copy` and `disable_web_page_preview=Default(...)` in the `answer` / `reply`
   shortcuts. Today they carry only `json_schema_extra={"deprecated": True}` and a docs note (e.g.
   `aiogram/types/message.py`, `forward_date`); nothing warns at runtime.

## Scope

**In:**
- **Mutation:**
  - `MutableTelegramObject.__setattr__` (`aiogram/types/base.py`) calls `warn_deprecated(<mutation id>)` and then
    the base `__setattr__`;
  - private names (`_bot`, set by `BotContextController.model_post_init`) and pydantic internals are exempt;
  - aiogram's own code must not mutate these objects: audit `utils/keyboard.py`, `utils/media_group.py`,
    `utils/formatting.py`, `client/bot.py` and the shortcuts, and switch them to construction or `model_copy`.
- **API-ledger fields (`AiogramApiDeprecationWarning`):**
  - generate the warnings from the `.butcher` deprecation markers (the same markers that produce `json_schema_extra
    deprecated`), never by hand-editing `aiogram/types` / `aiogram/methods`;
  - **types:** warn when user code reads a deprecated field;
  - **methods:** warn when a deprecated parameter is passed with a non-`None` value at construction, including
    through `Bot.*` methods and shortcuts, which build method objects;
  - **deprecated entities:** warn when they are constructed;
  - updates decoded from Telegram must not warn just because Telegram still sends a deprecated field.
- **API-ledger registry entries:** generate `api-ledger` entries into `registry.toml` from the `.butcher` markers,
  at A-11's granularity and in A-11's id block. A-11 proposes one entry per affected Bot API object or method, listing
  its removed fields, plus one per removed entity, in AG4800–AG4999; use `generated = true` and append-only ids. Add the generator script
  and a CI-style test that it is up to date.

**Out:**
- D100 positional calls: no runtime warning (checker-only, I-18; documented in 3x-24).
- 4.0 immutability and ledger reset themselves: C-10 / C-26 / B-04.

## Checklist

- [ ] Baseline with A-05 on `update.realistic` decode, `request.sendMessage.plain` construction and
      `keyboard.inline.30`. The mutation hook and field warnings must not slow the happy path measurably.
- [ ] Mutation hook, the exemptions and the internal-mutation audit. Prove there are no internal mutations by
      running the full suite under the 3x-20 guard.
- [ ] Decide the ledger-field mechanism. Proposed default:
  - for **types**, pydantic `Field(deprecated=typing_extensions.deprecated(msg,
    category=AiogramApiDeprecationWarning))`, emitted by butcher. It warns on attribute read only, which is the
    reliance signal, and stays silent on decode and `model_dump`;
  - for **methods**, a class-level `__deprecated_params__: frozenset[str]` emitted by butcher, checked against
    `model_fields_set` in one place in `TelegramMethod.model_post_init`.

  Check the pydantic floor (≥ 2.7 supports `deprecated=`). Record the choice in Notes and flag it to the owner if it
  needs a butcher-tool change.
- [ ] Internal reads of deprecated fields must not warn: audit `Message.send_copy`, the shortcuts and the `Bot`
      parameter translation (which maps `reply_to_message_id` → `reply_parameters`), and switch them to the
      replacement fields or a private accessor.
- [ ] Regenerate with `butcher apply all`. Commit config and output together.
- [ ] API-ledger entry generator and test. Count check: the generated entries together list every deprecation marker.
      122 fields plus 3 entities is the research count; record the actual one.
- [ ] Add triggers to 3x-20's sync-test table: one per base class for mutation, and a parametrised trigger over all
      `api-ledger` entries.
- [ ] 100% coverage. The full suite passes under the guard.
- [ ] Changelog fragment `CHANGES/<pr>.removal.rst`: "attribute assignment on mutable types and the Bot API fields
      deprecated during 3.x now warn; both go in 4.0".

## Acceptance criteria

- `InlineKeyboardButton(text="a", callback_data="b").text = "c"` emits one `AiogramDeprecationWarning` with the
  mutation id.
- `message.forward_date` on a decoded message warns, with `AiogramApiDeprecationWarning` and its ledger id.
- Decoding the A-04 corpus emits **no** warnings.
- `SendMessage(chat_id=1, text="x", reply_to_message_id=5)` warns once.
- A-05 `compare`: `update.realistic` decode and `request.sendMessage.plain` construction within +3% of the parent
  commit.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Warn on decode when a deprecated field is present | Telegram still sends some of them; users did nothing wrong | 16 §1 |
| Hand-written per-field warnings | 122 fields; regeneration reverts them | AGENTS.md |
| Keep plain `DeprecationWarning` for ledger fields | Must be the `AiogramApiDeprecationWarning` subclass | D72, R28 |

## Validation

```bash
uv run --extra cli butcher parse && uv run --extra cli butcher refresh && uv run --extra cli butcher apply all
git diff --exit-code
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases update.realistic,request.sendMessage.plain,keyboard.inline.30
```

## Workflow notes

- C-26 (4.0 removal inventory) cross-checks its list against the `api-ledger` entries generated here. A difference
  is a bug in one of the two.
- C-11 must import the `.butcher` changes.

## Notes
