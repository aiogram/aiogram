## Context

The chat-administration change modeled the *shape* of administration: statuses, custom titles,
tags, the membership reads. It deliberately did not model policy, and it said so — the fake
stores permissions and never enforces them.

What the PoC exposed is that "not enforced" and "not stored" are different things, and only the
first was intended. A bot does not need the fake to *refuse* a call for want of a right; it
needs to *read* the right it holds, because that is what its own branch is written against.
`getChatMember` was inventing that answer, which is the failure mode the toolkit's design doc
calls out as the worst kind: a green assertion that checks nothing.

`MemberState` already carried `status`, `custom_title`, `tag` and `until_date`. The two fields
that were missing are the two the Bot API's own member variants carry.

## Goals / Non-Goals

**Goals:**

- A test can declare what the bot, and any member, may do — before any call is made.
- `promoteChatMember` and `restrictChatMember` are truthful: what a test reads back is what
  the request granted.
- The answers match what the real API reports for the chat they are read in.
- The fake is never *more* permissive than Telegram in a way a test cannot notice.

**Non-Goals:**

- **Enforcing rights.** Unchanged and load-bearing: setting restrictive permissions does not
  make a later send fail, and an administrator without `can_delete_messages` can still delete
  messages here. A test that needs the rejection declares it with an override.
- Modelling *who* may grant what — the "can_be_edited" question, promotion chains, anonymous
  admin identities beyond the flag itself.
- A permission matrix over the sending methods. That is policy, and it stays out.

## Decisions

### D1. Rights live on `MemberState`, not on the conversion

`MemberState.rights` and `MemberState.permissions` are `None` when not stated. `None` on an
administrator means "not stated", and reads back as the ordinary administrator rights of the
chat's type; `None` on a restricted member means every permission denied, which is what a
restriction with no permissions passed amounts to.

Storing rather than inventing is the whole change: `promoteChatMember`, `restrictChatMember`
and a blueprint declaration all write the same field, and `getChatMember` reads it.

### D2. `promoteChatMember` stores the whole mask, every call

The Bot API sets the complete rights mask on every `promoteChatMember`, so a right the request
does not pass is not granted. The handler therefore stores the whole coerced mask rather than
merging into what was there — a second promotion replaces the first, exactly as at Telegram.

The demotion rule follows from the same reading: the Bot API documents demotion as "pass
`False` for all boolean parameters", and an omitted parameter is not granted either, so a
request in which *nothing* comes out true is a demotion to a plain member.

`is_anonymous` counts. It is a right like any other, and the old rule — which scanned only
fields named `can_*` — read `promote_chat_member(is_anonymous=True)` as a demotion and silently
stripped the administrator. Deriving the mask from `ChatAdministratorRights.model_fields`
rather than a name prefix fixes that and makes a right a future Bot API version adds flow
through unchanged.

### D3. Chat-type scoping happens where the chat type is known — on read

`CHAT_TYPE_SCOPED_RIGHTS` names the rights the Bot API reports only in some chat types.
`scoped_rights` is applied in `as_chat_member`, which is the only moment the chat type is in
hand: a right that cannot exist in that chat reads back as `None`, and a right that can reads
back as a plain boolean even when it was left unstated — which is how the real API answers and
what a bot writing `if member.can_pin_messages:` relies on.

*Consequence:* `as_chat_member` takes the chat type as a parameter. A membership object built
without knowing where the member holds it cannot be truthful about either field, so there is no
sensible default to give it.

### D4. `administrator_rights()` returns an *unscoped* mask

The factory a test calls is deliberately not scoped, even though the reader is. Scoping at
declaration time would mean stating a right explicitly grants *fewer* rights than saying
nothing at all:

```python
# In a channel, both of these must report `can_post_messages is True`.
set_member(channel, bot, rights=administrator_rights(can_post_messages=True))
set_member(channel, bot, status=ChatMemberStatus.ADMINISTRATOR)
```

One declaration is therefore truthful in every chat, and the chat decides what it reports.

The permissive default itself — everything a moderator needs, minus the two things a chat owner
grants deliberately, `can_promote_members` and stories — is built in exactly one place, on top
of an all-`False` floor derived from `model_fields`. A right a future Bot API version adds
defaults to `False` in both masks rather than breaking the call.

### D5. `bot_status` and `members[blueprint.bot]` are both accepted, together are rejected

Both spellings are natural — `bot_status=ADMINISTRATOR` reads well when the bot is the only
interesting member, and the `members` mapping reads well when it is one of several. Accepting
both and letting one win silently is the kind of thing a test author discovers three failures
later, so passing them together raises, **including** when `bot_status` is the default
`MEMBER`: an explicit argument is a statement, not a fallback.

*Alternative rejected:* merging them, with `bot_status` as a default the `members` entry
overrides. It makes the two spellings look composable when the only composition is a
contradiction.

### D6. `set_member` is a separate verb from the `members=` shorthand

The shorthand says what a user *is*; `set_member` says what they may **do**. Keeping them apart
means the common declaration stays a one-line mapping, and the interesting one — "the bot is an
admin but cannot delete messages" — is a call that names the fields it sets.

Passing `rights` or `permissions` implies the status that carries it, so the interesting case is
still one call. An explicit `status` wins over the implication. Passing both `rights` and
`permissions` for one member raises: they belong to different `ChatMember` variants, so there is
no member the pair describes.

### D7. One owner guard, shared by three methods

`_not_the_owner` is the single rule behind `banChatMember`, `restrictChatMember` and
`promoteChatMember`, because Telegram answers all three with the same "can't remove chat owner".

Sharing it also closes the way *around* it that the first version left open: banning the owner
first turned them `KICKED`, which a guard checking only `CREATOR` on promote no longer
recognised — so the ex-owner could then be promoted at will. With the guard on all three, the
first step already fails.

This is not the permission matrix returning. It is one thing the *subject* of the call makes
impossible, not a check of what the caller is allowed to do.

## Risks / Trade-offs

- **"Rights are stored" reads as "rights are enforced"** → the same hazard the previous change
  named, now with more surface. Mitigated by keeping the non-enforcement requirement and its
  scenario in the spec, and by the documentation showing the override recipe for a rejection.
- **Scoped reads look like data loss** → a test that declares `can_manage_topics=True` on a
  *group* administrator reads back `None`. That is the real API's answer, and the docs say so;
  the alternative is a fake that is truthful nowhere.
- **`as_chat_member` gained a required parameter** → it is internal to the world, and every
  caller has the chat in hand. Giving it a default would have reintroduced exactly the untruth
  it exists to remove.
- **The permissive default is a judgement call** → what "an ordinary administrator" can do is
  not defined by the Bot API. It is defined once, in `_ORDINARY_ADMIN_RIGHTS`, next to the
  factory, so it can be argued with in one place.

## Migration Plan

Additive at the declaration level. `getChatMember` answers change for administrators: rights are
now what was granted, and out-of-scope rights are `None` rather than `True`. Nothing in the
suite depended on the old answers, and the changelog states the new rule.

## Open Questions

- Should a declared `rights` mask on a `CREATOR` do anything beyond `is_anonymous`? The Bot
  API's `ChatMemberOwner` carries no other right, so today only `is_anonymous` is read off it.
  If a future version grows the variant, the storage is already there.
