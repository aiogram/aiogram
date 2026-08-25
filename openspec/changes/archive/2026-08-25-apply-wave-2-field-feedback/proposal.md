## Why

The same production Mafia-game group bot that drove the first round of feedback was run
against the toolkit again once that round had shipped. The second round is a different kind
of list: nothing was missing this time, and nothing raised where it should have worked.
Every finding is a place where the toolkit answered *plausibly* and wrongly, and where the
test therefore passed.

```python
await bot.send_message(chat_id=player.id, text="You are the Mafia.")
# TelegramBadRequest: Bad Request: chat not found
```

That is the shape of all of it. The bot handles "chat not found" — it is what Telegram says
when a player has never opened the DM or has blocked the bot — so its own `except
TelegramBadRequest` caught the toolkit's answer, ran the blocked-player branch, and the test
that was written to check the *role announcement* passed while asserting on nothing of the
kind. The blueprint had simply never declared that private chat.

The rest, all found the same way:

- `edit(fields={"reply_to_message": stored})` copied the stored message while
  `send(fields={"reply_to_message": stored})` aliased it, so the same line meant two
  different things depending on which trigger carried it, and an edit to the target stopped
  showing through the reply.
- A "Play" button carrying `?start=game-42&startapp=game-42` — the shape Telegram itself
  hands out, so that a client which cannot open the Mini App still opens the bot — was
  refused as a `startapp` link the toolkit does not simulate.
- `chat.messages[-1]` pointed at a message with a *lower* id than its neighbours after an
  update built in another environment was fed in, and `wait_for_message` returned that stale
  message as "the newest match", because newest was implemented as last-in-list.
- A demoted administrator kept their `custom_title`, so the next promotion resurrected a
  title nobody had granted — a state `getChatMember` cannot report, since
  `ChatMemberMember` has no field for one.
- `restrict_chat_member(permissions=ChatPermissions(can_send_other_messages=True))` produced
  a member who may send stickers but not text. Real Telegram will not do that; the bot gated
  itself on `can_send_messages` and took the branch the fake had invented for it.
- `world.chats = {...}`, the obvious way to rebuild a world in a fixture, replaced the
  registry that hands each chat its way back to the world with a plain `dict`. Every chat
  went in unwired and every message stored afterwards was unbound — surfacing much later as
  a shortcut raising on a message that looks perfectly ordinary.
- Every wait in the suite carried its own `timeout=`, because the environment had no way to
  be told once — and the chat-scoped waits, which are the ones tests actually write, had no
  way to be told at all. `description` was keyword-only, so the parameter that is the only
  thing a failure message can say about a lambda was the one nobody passed.

## What Changes

- **One rule for everything a test hands into the world.** `mounting.owned_or_copied` is
  that rule: a value already owned by this environment's bot passes through by identity, and
  everything else is copied. `send`, `edit` and every other trigger field now go through it,
  so world-owned values keep their identity in `fields=` on every path.
- **An explicit `start` wins** over a co-occurring `startapp`, `startgroup` or
  `startchannel`, in either query order, because that is what a real client does. A
  start-ish parameter with no `start` beside it is still refused by name.
- **A chat's messages are ordered by `message_id`.** `add_message` places rather than
  appends, so a message carried in from another environment cannot leave `chat.messages[-1]`
  pointing at something old; and `wait_for_message` returns the match with the highest
  `message_id` rather than the last one the list holds.
- **A demotion drops the custom title.** `tag` survives it, because `tag` is a field of
  `ChatMemberMember` as much as of the administrator variants — it belongs to the membership,
  not to the status.
- **An undeclared chat on the outbound path is a setup gap, not a Bad Request.** It raises
  `WorldLookupError` enumerating the chats this world does have and pointing at
  `add_private_chat` / `ensure_private_chat`, and the message names
  `env.on(SendMessage).raises(TelegramBadRequest, "Bad Request: chat not found")` as the way
  to test the real API branch. The outbound path deliberately does not open a private chat on
  demand the way the actor paths do: a real bot cannot write first.
- **`restrictChatMember` and `setChatPermissions` apply the Bot API's couplings**, so the
  permissions read back may be broader than the mask passed, unless the call sets
  `use_independent_chat_permissions=True`.
- **`world.chats` is a registry however it is assigned**, guarded by `World.__setattr__`
  rather than installed once in `__post_init__`.
- **`BotTestEnvironment(..., default_wait_timeout=...)`** is the single place to set the
  default for `wait_for` and for every chat and topic `wait_for_message`; a per-call
  `timeout=` still wins. `description` becomes the **second positional** parameter of all
  three waits, and still works as a keyword.

Two findings were answered with documentation rather than code: the `looptime` recipe for
bots whose slowness is their own `asyncio.sleep`, verified rather than speculated about, and
the reminder that `Blueprint(default=...)` has to match the production `Bot(default=...)`
because a mismatch never raises.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the ordering of a chat's messages and the newest-match rule
  become stated behavior; the setup-gap rule extends to the outbound chat lookup; deep-link
  precedence, the permission couplings, the fate of `custom_title` and `tag` on demotion, and
  the environment-wide wait timeout are all stated.

## Impact

- **Code**: `mounting.py` gains `owned_or_copied`; `actors.py` and `world.derive_message`
  both use it; `actors.py` checks `start` before the policy table; `world.py` sorts on
  insert, returns the highest-id match, derives `default_wait_timeout` on `ChatState` and
  `TopicState`, and guards `chats` in `World.__setattr__`; `modeling.py` raises
  `WorldLookupError` from `resolve_chat` with an enumerating message, clears `custom_title`
  on demotion, and adds `granted_permissions`; `environment.py` takes
  `default_wait_timeout`; `waiting.py` exports `DEFAULT_WAIT_TIMEOUT`.
- **Tests**: new suites in `test_modeling.py` (the undeclared outbound chat),
  `test_chat_administration.py` (couplings, demotion), `test_waiting.py` (positional
  description, default timeout, newest-by-id), `test_deep_links.py` (start precedence),
  `test_triggers.py` (edit/send parity), `test_world.py` (the registry guard),
  `test_environment.py` (id-ordered insertion), plus `test_looptime_recipe.py` verifying the
  documented recipe end to end.
- **Docs**: eight amendments across `docs/dispatcher/testing.rst`, plus the `looptime`
  section and the `Blueprint(default=...)` note.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry — the
  toolkit is unreleased, so there is no released behavior to describe a change to.
- **Risk**: the two behavioral reversals — `chat not found` becoming a `WorldLookupError`,
  and permissions reading back broader than they were passed — will fail tests written
  against the previous answers. Both fail loudly and both say what to do, which is the point:
  a test that relied on either was asserting on a world Telegram cannot produce.
