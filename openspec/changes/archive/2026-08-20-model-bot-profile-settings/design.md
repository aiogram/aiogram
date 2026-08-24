## Context

Thirteen methods configure and read the bot's own profile. All of them are pure storage on
Telegram's side: there is no validation worth reproducing, no service message, no update,
and no interaction with any other part of the API. That makes them the one cluster where
the fake can be *faithful by construction* rather than approximately faithful — a rare
property in this package.

They also share one shape. `setMyCommands(commands, scope, language_code)` and
`setMyDescription(description, language_code)` differ only in what is stored and how many
key components there are. `setChatMenuButton(chat_id, menu_button)` is the same idea keyed
by chat instead of scope.

The existing world already carries `bot_user`, which is the natural anchor: the bot's
profile belongs next to the bot's identity.

## Goals / Non-Goals

**Goals:**

- Make startup configuration code — the `setMyCommands` block almost every bot has —
  assertable.
- Faithful key semantics, including the parts that surprise people: commands do not fall
  back to a broader scope, while the localized texts do fall back by language.
- Sensible unconfigured behavior, so a bot that only *reads* its profile works without any
  test setup.

**Non-Goals:**

- Modeling what commands a *given user* would see. That is Telegram's client-side
  resolution over scopes, not something `getMyCommands` exposes, and inventing it would
  put the fake at odds with the real API.
- Validating command names, description lengths, or the documented scope constraints
  (`setMyCommands` rejecting some scope/language combinations). Policy, not shape.
- The bot's profile *photo* (`setMyProfilePhoto`, `removeMyProfilePhoto`) — media
  processing, and no getter exists to read it back.

## Decisions

### D1. One `BotProfileState`, dict-per-field

```
BotProfileState:
    commands: dict[key, list[BotCommand]]
    name: dict[str | None, str]
    description: dict[str | None, str]
    short_description: dict[str | None, str]
    default_admin_rights: dict[bool, ChatAdministratorRights]   # keyed by for_channels
    menu_buttons: dict[int | None, MenuButton]                  # None is the default
```

where `key` is a hashable tuple built from the `BotCommandScope` member's own fields plus
the language code (see D5). Normalizing to a tuple rather than storing the scope object
keeps lookups exact and hashable without depending on pydantic model equality.

*Alternative rejected:* a single `dict[str, Any]` keyed by method name. It would collapse
the per-field key shapes and make the getters guess.

### D2. Commands use exact keys; the localized texts fall back by language

The two halves of this cluster do *not* share lookup semantics, and reading the Bot API
documentation carefully is the only way to see it:

- **Commands** are exact. `getMyCommands` returns what was set for that exact scope and
  language, and an empty list otherwise. The fallback the docs mention ("higher level
  commands will be shown to affected users") is a statement about what *users* see, not
  about the getter's return value. Modeling a scope fallback here would make the fake
  disagree with the real API in the exact scenario someone would write a test for.
- **Name, description and short description** *do* fall back. Setting one with an empty
  `language_code` makes it apply "to all users for whose language there is no dedicated"
  value, so a getter for an unset language returns the default-language entry.
- **Menu buttons** fall back the same way: a chat with no dedicated button reports the
  default one.

An empty string clears the dedicated entry for that language rather than storing an empty
value, which is what the Bot API says it does — so the fallback resumes afterwards.

### D3. Defaults come from the documentation, not from synthesis

An unset value returns the documented empty value — `[]`, `""`, `MenuButtonDefault()`,
`ChatAdministratorRights` with every field `False` — and an unset bot name returns
`world.bot_user.first_name`, which is what Telegram falls back to.

This is why the change is worth making at all: today these getters return synthesized
objects, so a bot that branches on "are commands already registered?" takes the wrong
branch in every test.

### D4. Blueprint declares an initial profile

`Blueprint.with_bot_profile(commands=…, name=…, …)` (frozen, like every other
declaration) so a test can start from a configured bot. `Blueprint.build()` deep-copies it
into the environment, inheriting the existing isolation guarantee with no new machinery.

### D5. Scope keys are built from the scope's own fields

Handlers receive the already-`Default`-resolved method object, so the scope arrives as a
real `BotCommandScope*` model. The key is built from *every* field that member declares,
not from a hand-read list of the ones known today — so a future variant carrying a new
identifying field keys correctly instead of silently colliding with its siblings.

This removes the need for a recognizer that raises on unknown members: there is nothing to
recognize. The parametrized test over every union member stays, now asserting that
distinct scopes produce distinct keys.

## Risks / Trade-offs

- **Two different lookup rules in one cluster (D2)** → an implementer could apply the
  command rule to the localized texts, or the reverse, and the mistake would look
  reasonable. Mitigation: scenarios in the spec pin both behaviors, and the shared read
  helper takes the fallback rule as an explicit argument rather than assuming one.
- **Someone will expect a command scope fallback (D2)** → a user may report the absence as
  a bug. Mitigation: the docs section states it explicitly and says why, and the spec has a
  scenario naming the behavior.
- **Thirteen thin handlers is still thirteen handlers** → repetitive code. Mitigation: a
  shared read/write pair parametrized by field name and key extractor, so the per-method
  code is one line each.
- **Marginal fidelity risk if Telegram ever adds server behavior here** → e.g. rejecting
  malformed commands. Accepted: policy enforcement is an explicit non-goal of the whole
  toolkit, and a test wanting that failure writes an override.

## Migration Plan

Purely additive. A test today asserting on a synthesized `getMyCommands` result would newly
see an empty list — which is the defect being fixed, and the changelog says so.

## Open Questions

- Should `getChatMenuButton` reject a non-private `chat_id` the way Telegram does? Leaning
  yes, since it is a one-line check against existing `ChatState.type` and catches a real
  mistake; deferred to implementation if it proves noisy.
