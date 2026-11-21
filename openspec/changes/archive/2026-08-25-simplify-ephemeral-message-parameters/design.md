## Context

`butcher` renders a shortcut by splicing each `fill:` value from
`.butcher/types/<Type>/aliases.yml` verbatim as the right-hand side of a keyword
argument. It never parses the expression, so a fill can be a literal, an attribute
access, a conditional, or a method call. `reply_parameters` already exploits this:
its fill is `self.as_reply_parameters()`, a call into a hand-written method that
`butcher` preserves because it sits outside the generated block.

The `ephemeral_message_parameters` fill added in the 10.3 bump did not follow that
pattern — it inlines the whole conditional, so the rule is duplicated into every
generated shortcut body.

A filled parameter is removed from the shortcut's signature. An explicit value
therefore arrives through `**kwargs` and collides:

```
>>> message.reply("x", ephemeral_message_parameters=params)
TypeError: SendMessage() got multiple values for keyword argument
           'ephemeral_message_parameters'
```

## Goals / Non-Goals

**Goals:**

- One named, testable, publicly callable place that builds `EphemeralMessageParameters`.
- A supported way to set `callback_query_id` and `replace_callback_query_message`.
- Stop sending `ephemeral_message_parameters` to methods that do not accept it.

**Non-Goals:**

- Changing which user the reply is addressed to. `self.from_user.id` stays.
- Making fills overridable by caller-supplied values. The `answer()` escape hatch
  stays as-is; changing it would require new `butcher` semantics and would touch
  every generated shortcut.
- Adding send shortcuts to `CallbackQuery`.
- Touching `InaccessibleMessage`, which is a sibling type with its own simpler
  `as_reply_parameters` and is never ephemeral.

## Decisions

### Helper on `Message`, taking the optional fields as arguments

`callback_query_id` and `replace_callback_query_message` originate on
`CallbackQuery`, and `Message` holds no back-reference to the query that triggered
it — unlike `guest_query_id`, which is a `Message` field and is why
`answer_guest_query` can fill it. A `Message`-side helper therefore cannot derive
either value from `self`; it accepts them instead:

```python
def as_ephemeral_message_parameters(
    self,
    callback_query_id: str | None = None,
    replace_callback_query_message: bool | None = None,
) -> EphemeralMessageParameters | None:
    ...
```

Returning `None` for a non-ephemeral message preserves the current fill semantics
exactly — the fill becomes `self.as_ephemeral_message_parameters()` and yields
`None` where the inline conditional did.

*Alternatives considered.* A helper on `CallbackQuery` would see both inputs and
could enforce the `replace_callback_query_message` rule, and send shortcuts on
`CallbackQuery` would be the most ergonomic. Both add API surface to a second type
for a case the caller can already express with `message.answer(...)`. Deferred; the
`Message` helper does not block either later.

### Exclude the six shortcuts in `.butcher` rather than in `butcher` itself

Only 14 send methods declare `ephemeral_message_parameters`. `SendDice`, `SendPoll`,
`SendGame`, `SendInvoice`, `SendMediaGroup` and `SendPaidMedia` do not, and
`TelegramMethod` allows extras, so the value is carried into the request:

```
>>> eph.reply_dice().model_dump(exclude_none=True).keys()
['chat_id', 'ephemeral_message_parameters', 'protect_content', 'reply_parameters']
```

The alternative — teaching `butcher` to drop any fill whose key is not a field of the
target method — is the general fix and kills the whole class of bug. Listing the six
in `.butcher/types/Message/aliases.yml` is local, explicit, reviewable, and works with
the released generator, so it is what this change ships. See Open Questions for the
generator-side follow-up.

### Keep `self.from_user.id`

On an ephemeral `Message`, `from_user` is the bot and `receiver_user` is the human
viewer, so the fill emits the bot's own id while the sibling `edit_ephemeral_*` fills
use `receiver_user`. Confirmed intentional by the maintainer; this change preserves
the behaviour and does not re-open it.

## Risks / Trade-offs

- **The six excluded shortcuts silently change their payload** → The removed
  parameter was never accepted by those methods, so no working call can regress.
  Covered by a test asserting the field is absent from `model_extra`.
- **A future Bot API version adds the field to one of the six** → The exclusion list
  goes stale and the shortcut quietly loses a valid fill. Mitigated by a test that
  cross-checks the exclusion list against `model_fields` of each target method, so it
  fails when the API catches up.
- **The helper is hand-written inside a generated module** → Same exposure as
  `as_reply_parameters`, which has survived many regenerations; `butcher` only
  rewrites its own marked block. Verify by re-running `butcher apply` and confirming
  a clean diff.

## Migration Plan

None required — no public signature changes. The new helper is additive.

## Open Questions

- `butcher` should drop fills whose key is not a field of the target method, retiring
  the exclusion list this change adds. This turns out to be a one-line slip rather
  than an invasive change: `parsers/entities/resolvers/aliases.py` already computes
  the filtered `fill` and uses it to decide which parameters stay in the shortcut
  signature, but stores the *unfiltered* dict under `"fill"`, which
  `codegen/transformers/types.py` then splices into the generated call. Changing
  `"fill": alias["fill"]` to `"fill": fill` was verified to drop the parameter from
  exactly the six shortcuts, correct their docstrings, and leave every other file in
  the project untouched. Belongs in its own butcher change, not here.

### Deprecated parameters stay where they were

A deprecated parameter must keep the position it had before this release; dropping
one breaks callers that still pass it. That cuts both ways here:

- `receiver_user_id` is added to `ignore: &ignore-reply`. Before Bot API 10.3 the
  `reply` fill consumed it, and `butcher` omits a filled parameter from the shortcut
  signature, so `reply_*` never accepted it. Handing its role to
  `ephemeral_message_parameters` freed the name and `butcher` began emitting it as a
  *new* parameter. Ignoring it restores the pre-10.3 signature rather than removing
  anything.
- `callback_query_id` is **not** ignored. It was already an ordinary parameter of the
  `reply_*` shortcuts before 10.3, so it stays exactly where it was.
