## Context

This change is unusual in the plan: it is mostly a **correctness fix dressed as a feature**.
`GetChat` and `GetChatMember` are already modeled, so tests already read chat and member
state back — they just read stale or fabricated values because the mutating methods were
never wired. The failure mode is the worst kind the design doc warns about: a green
assertion that checks nothing.

The pieces needed already exist:

- `ChatState` carries `id`, `type`, `title`, `username`, `first_name`, `last_name` and
  `members`; `handle_get_chat` converts it to `ChatFullInfo`.
- `MemberState` carries `status`, `custom_title` and `until_date`; the ban/promote/restrict
  handlers maintain it.
- `service_message(...)` was introduced for the forum topic methods and is exactly the
  helper the `new_chat_title` / `delete_chat_photo` messages need.

## Goals / Non-Goals

**Goals:**

- Make `getChat` and `getChatAdministrators` truthful after any modeled mutation.
- Emit the service messages Telegram emits, so handlers that filter on them are testable.
- Store the fields `ChatFullInfo` exposes that the world currently cannot fill.

**Non-Goals:**

- **Enforcing permissions or administrator rights.** This is the load-bearing non-goal.
  Setting restrictive `ChatPermissions` does not make a later `sendMessage` fail, and
  promoting a bot without `can_delete_messages` does not make `deleteMessage` fail. The
  permission matrix is policy; the design doc rules it out for the whole toolkit, and this
  change does not reopen it.
- Chat photos as media. `setChatPhoto` stays record-only; only *deletion* is modeled,
  because deletion is a state transition (`photo` → `None`) with an observable service
  message, while setting one would require fabricating a `ChatPhoto` from an uploaded file.
- Sender-chat bans and verification badges — nothing reads them back.

## Decisions

### D1. Grow `ChatState` with the fields `ChatFullInfo` already exposes

Add `description`, `permissions`, `photo` and `sticker_set_name`. Each is declarable on
the blueprint and read by `handle_get_chat`. This is deliberately conservative: only fields
a modeled method writes *or* a declared world needs, not the whole of `ChatFullInfo`.

### D2. Reuse `service_message` from the forum work

`setChatTitle` and `deleteChatPhoto` emit through the same helper the forum methods use, so
the service message gets a real `message_id`, lands in `ChatState.messages`, and is visible
to `env.calls`-independent state assertions. No new machinery, and the shape stays
consistent with the topic service messages already shipped.

*Consequence worth stating:* the emitted message counts in the chat's message list. A test
asserting "the chat has exactly one message" after a rename will see two. That matches
Telegram, and the spec scenario makes it explicit.

### D3. Membership reads are derivations, not stored lists

`getChatAdministrators` filters `members` by `ChatMemberStatus.CREATOR` /
`ADMINISTRATOR` and converts through the same path `getChatMember` uses;
`getChatMemberCount` returns `len(members)`. Nothing is cached, so the answer cannot drift
from the state the ban/promote handlers maintain.

*Alternative rejected:* a separate `administrators` list on `ChatState`. Two sources of
truth for one fact, and the existing handlers would have to update both.

### D4. Errors only where a test would provoke them

`TelegramBadRequest` is raised for: an unknown chat or user, an administrative action on a
private chat, and a custom title for a non-administrator. These are mistakes a bot author
actually makes and would want a test to catch. Everything else — a title longer than
Telegram allows, an unsupported permission combination — is policy and stays permissive.

### D5. `MemberState.tag` is a new field, `custom_title` is not

`custom_title` already exists and is simply unwired. `setChatMemberTag` needs one new
field. Both are surfaced by the existing `getChatMember` conversion, so the change is two
writes and one field.

They are not interchangeable, and the generated types say so: `custom_title` exists on
`ChatMemberOwner` / `ChatMemberAdministrator`, while `tag` exists on `ChatMemberMember` /
`ChatMemberRestricted`. Writing the wrong one would produce a member object whose
annotation silently disappears on conversion, so each method rejects the status it does not
apply to.

### D6. `getChatAdministrators` omits other bots by default

The Bot API omits bots other than the caller unless `return_bots` is passed. That is a
documented filter rather than server folklore, it is one line, and without it a test with a
second bot in the chat would assert against a list Telegram would never return.

## Risks / Trade-offs

- **"Permissions are stored" reads as "permissions are enforced" (Non-Goals)** → someone
  writes a test expecting a restricted send to fail, and it passes instead. Mitigation: an
  explicit spec requirement stating the non-enforcement with a scenario, plus a docs
  paragraph pointing at overrides for the rejection case.
- **Service messages change message counts (D2)** → existing tests that count messages in a
  chat could newly fail if they also rename it. Mitigation: called out in the changelog;
  in practice no current test does both.
- **`ChatState` growth invites more growth** → the next reader adds another `ChatFullInfo`
  field "while we're here". Mitigation: D1 states the rule — a field earns its place by
  being written by a modeled method or declared on a blueprint.
- **`getChatAdministrators` ordering** → Telegram returns the creator first; the fake must
  too, or tests indexing `[0]` will be flaky across dict iteration. Mitigation: sort
  creator-first explicitly and cover it with a scenario.

## Migration Plan

Additive, with two observable behavior changes worth a changelog line: `getChat` now
reflects prior mutations instead of returning stale declared values, and a rename appends a
service message to the chat.

## Open Questions

- Should `deleteChatStickerSet` on a chat with no sticker set raise, or succeed as a no-op?
  Leaning no-op, matching the permissive default; revisit if a real bot depends on it.
