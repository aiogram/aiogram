## 1. Rights as membership state

- [x] 1.1 Add `MemberState.rights` and `MemberState.permissions`, both `None` when unstated
      (design D1)
- [x] 1.2 Add `MemberSpec.rights` / `.permissions` and carry them through `Blueprint.build()`
- [x] 1.3 Read them in `MemberState.as_chat_member`: an unstated administrator gets the
      ordinary rights, an unstated restriction denies everything
- [x] 1.4 Tests: a declared partial-rights administrator reads back as declared; the declared
      rights reach `getChatAdministrators` as well

## 2. The masks

- [x] 2.1 Add `mask(model, source, coerce=...)`, reading a flat boolean mask off any source by
      `model_fields`, so a future right flows through every reader unchanged (design D2)
- [x] 2.2 Add `no_administrator_rights()` — every right denied — as the floor both masks build
      on, and use it for the unset `getMyDefaultAdministratorRights` answer
- [x] 2.3 Add and export `administrator_rights(**overrides)`, deliberately unscoped (design D4)
- [x] 2.4 Tests: an administrator declared without rights carries the ordinary ones

## 3. Chat-type scoping

- [x] 3.1 Add `CHAT_TYPE_SCOPED_RIGHTS` naming which rights the Bot API reports where
- [x] 3.2 Add `scoped_rights(rights, chat_type)` and apply it on read (design D3)
- [x] 3.3 Pass the chat type into `as_chat_member` from `getChatMember` and
      `getChatAdministrators`
- [x] 3.4 Tests: a supergroup administrator, a channel administrator, and rights granted
      through `promoteChatMember` are all scoped

## 4. Declaring the bot's standing

- [x] 4.1 Accept `bot_status` on `add_group`, `add_supergroup` and `add_channel`
- [x] 4.2 Accept `blueprint.bot` as a key of `members`, and skip appending the default entry
      when it is there
- [x] 4.3 Reject passing both, including when `bot_status` is `MEMBER` (design D5)
- [x] 4.4 Tests: both spellings reach `getChatMember` on the bot's own id; the default is still
      `MEMBER`; declaring both raises

## 5. `Blueprint.set_member`

- [x] 5.1 Add `set_member(chat, user, *, status, rights, permissions, custom_title, tag)`,
      amending an existing declaration or adding one (design D6)
- [x] 5.2 Imply `ADMINISTRATOR` from `rights` and `RESTRICTED` from `permissions`; let an
      explicit `status` win
- [x] 5.3 Reject `rights` and `permissions` together
- [x] 5.4 Tests: the bot declared to lack a right; a restricted member declared; amending a
      member declared by the shorthand; the rejection

## 6. Persisting what a call granted

- [x] 6.1 `handle_promote`: store the whole coerced mask, derived from
      `ChatAdministratorRights.model_fields` rather than a `can_` name prefix (design D2)
- [x] 6.2 Demote only when nothing in the mask comes out true, so `is_anonymous=True` keeps the
      administrator
- [x] 6.3 `handle_restrict`: store the permissions the request carried and clear any rights
- [x] 6.4 Tests: promote grants exactly what was asked for; a second promotion replaces the
      first; `is_anonymous` alone keeps the administrator; a promotion granting nothing demotes;
      a demoted administrator can be promoted again; restrict persists its permissions and does
      not keep the caller's object; restricting an administrator drops their rights

## 7. The owner guard

- [x] 7.1 Add `_not_the_owner`, shared by ban, restrict and promote (design D7)
- [x] 7.2 Raise Telegram's own "can't remove chat owner"
- [x] 7.3 Tests: the owner cannot be promoted, demoted, banned or restricted, and banning is
      not a way around the promote guard

## 8. Documentation

- [x] 8.1 Extend the "Chat administration" section with `bot_status`, the `members` spelling and
      why combining them raises
- [x] 8.2 Show `set_member` and `administrator_rights`, and state that the mask is unscoped
      while the *reads* are scoped
- [x] 8.3 State that promotion persists the whole mask, that a promotion granting nothing is a
      demotion, and that the owner is protected
- [x] 8.4 Add `administrator_rights` and `MemberState` to the API reference; build docs and fix
      any new warnings

## 9. Release readiness

- [x] 9.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry,
      which states that rights are granted as a whole and reported per chat type
- [x] 9.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview
      aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q
      --cov=aiogram --cov-report=term-missing` at 100%
- [x] 9.3 Confirm the "permissions are stored but not enforced" scenarios still pass unchanged
