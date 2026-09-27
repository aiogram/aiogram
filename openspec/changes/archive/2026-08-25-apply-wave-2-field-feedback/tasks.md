## 1. One rule for what enters the world

- [x] 1.1 Add `mounting.owned_or_copied(value, *, owner, bind=None)`: identity for what the
      owner already owns, `detached_copy` for everything else, walking `dict` and `list` to
      find a world object nested inside (design D1)
- [x] 1.2 Reduce `actors._detached` to a call to it, deleting the duplicated rule
- [x] 1.3 Route `derive_message`'s `changes` through it with `bind=bot`, so an edit aliases
      what a send aliases
- [x] 1.4 State it in the `mounting` module docstring as the third half of the policy — the
      boundary inwards, where the two directions are mixed
- [x] 1.5 Tests: `edit(fields={"reply_to_message": stored})` keeps the identity `send` keeps;
      two fields naming one stored object still share it; a value owned by *another*
      environment is still copied

## 2. Deep links: an explicit `start` wins

- [x] 2.1 Classify by `("start", *_QUERY_PARAM_KINDS)` rather than by policy-table order
      (design D2)
- [x] 2.2 Say so in the `follow_deep_link` docstring, which already promised it
- [x] 2.3 Tests: `?start=x&startapp=y` and `?startapp=y&start=x` both follow as a start
      carrying `x`, over `t.me` and `tg://resolve` alike; `?startapp=y` alone is still
      refused by name; `?startgroup=true` alone still classifies as `startgroup`

## 3. A chat's messages are ordered by id

- [x] 3.1 `ChatState.add_message` inserts by `message_id`, scanning backwards from the end so
      the append case costs one comparison (design D3)
- [x] 3.2 Point at it from `_register_carried_message`, which is the one producer that can
      arrive out of order
- [x] 3.3 `_wait_for_message` returns the match with the highest `message_id` rather than the
      last one the view holds (design D4)
- [x] 3.4 Tests: a carried message older than the chat's newest lands in order and does not
      become `messages[-1]`; a reversed list still yields the newest match

## 4. Demotion drops the title, not the tag

- [x] 4.1 Clear `custom_title` when a promotion granting nothing demotes (design D7)
- [x] 4.2 Leave `tag` alone, and state the model-level reason in the handler docstring
- [x] 4.3 Tests: a demotion clears the title so a later promotion cannot resurrect it; a
      demotion keeps the tag, and `getChatMember` reports it on the plain-member variant

## 5. An undeclared chat on the outbound path

- [x] 5.1 `resolve_chat` raises `WorldLookupError` rather than `ApiRejection` (design D5)
- [x] 5.2 Build the message: enumerate the declared chats with type and readable name, or say
      the world declares none
- [x] 5.3 Add the declared-user hint naming `blueprint.add_private_chat`,
      `env.world.ensure_private_chat` and "have the user write first"
- [x] 5.4 Name the escape hatch in the message itself:
      `env.on(<Method>).raises(TelegramBadRequest, 'Bad Request: chat not found')`
- [x] 5.5 State in the docstring why this path does not open a private chat on demand while
      the actor paths do
- [x] 5.6 Tests: the error type; the enumeration; the declared-user hint; the empty world; a
      chat with no readable name; an unknown `@username`; the override recipe actually
      exercising the bot's `except TelegramBadRequest` branch; the actor path still opening a
      chat

## 6. Permission couplings

- [x] 6.1 Add `granted_permissions(permissions, use_independent_chat_permissions)` applying
      the couplings both methods document (design D6)
- [x] 6.2 Fill the three field-level defaults after the couplings, and independently of the
      switch, since the Bot API states them on `ChatPermissions` rather than on the methods
- [x] 6.3 Use it from `handle_restrict` and `handle_set_chat_permissions`, returning a
      `model_copy` so the caller's object is untouched and extra fields survive
- [x] 6.4 Tests: each media permission implies every message kind; polls imply messages only;
      `use_independent_chat_permissions=True` stores the mask as passed; each default follows
      its source under both settings; a coupling feeds the defaults that follow it;
      `setChatPermissions` applies the same couplings; the caller's object did not grow

## 7. `world.chats` stays a registry

- [x] 7.1 Replace `World.__post_init__` with a `__setattr__` that converts any non-registry
      mapping assigned to `chats` (design D8)
- [x] 7.2 Tests: assigning a plain `dict` after construction keeps the wiring, the bot binding
      and the message binding; assigning the registry itself is a no-op; the declared mapping
      is a registry from construction

## 8. One wait timeout per environment

- [x] 8.1 Add `waiting.DEFAULT_WAIT_TIMEOUT` as the single floor under every wait
- [x] 8.2 Add `World.default_wait_timeout`, `compare=False` because it is configuration and
      not state (design D9)
- [x] 8.3 Derive `ChatState.default_wait_timeout` and `TopicState.default_wait_timeout` from
      it, with a fallback for a chat or topic outside any world
- [x] 8.4 Add `BotTestEnvironment(..., default_wait_timeout=...)` and use it in `wait_for`
- [x] 8.5 Make `timeout` optional on all three waits, so an explicit one still wins
- [x] 8.6 Tests: `wait_for`, a chat wait and a topic wait all honor it; an explicit `timeout=`
      wins; the default default is five seconds; a loose `ChatState` and `TopicState` fall back

## 9. `description` is positional

- [x] 9.1 Move `description` to the second positional parameter of
      `BotTestEnvironment.wait_for` (design D10)
- [x] 9.2 Add it in the same position to `ChatState.wait_for_message` and
      `TopicState.wait_for_message`, and use it as the "waiting for …" phrase
- [x] 9.3 Tests: all three take it positionally; `wait_for` still takes it as a keyword

## 10. Documentation

- [x] 10.1 Scope "a user's own private chat opens on demand" to the user-driven paths, and
      state that the bot's outbound calls open nothing and why
- [x] 10.2 Add the outbound undeclared chat to the `WorldLookupError` list in "When a call
      fails", and name the `env.on(...).raises(...)` recipe for the real API branch
- [x] 10.3 Document deep-link precedence: `start` wins over a co-occurring start-ish
      parameter, and a start-ish parameter alone is still refused
- [x] 10.4 Update the `wait_for` examples to the positional `description`
- [x] 10.5 Document `BotTestEnvironment(..., default_wait_timeout=...)` as the single place to
      set it, with a `bot_env` fixture override
- [x] 10.6 State the newest-match rule as highest `message_id`, not last-in-list
- [x] 10.7 Document the permission couplings and `use_independent_chat_permissions`
- [x] 10.8 Document that a demotion drops `custom_title` while `tag` survives
- [x] 10.9 Verified `looptime` recipe, with the `interval` caveat and the note on what a fake
      clock does not virtualize
- [x] 10.10 Note that `Blueprint(default=...)` must match the production `Bot(default=...)`,
      because a mismatch never raises
- [x] 10.11 `tests/test_testing/test_looptime_recipe.py` exercises the documented recipe where
      `looptime` is installed and skips cleanly where it is not, so the recipe cannot rot

## 11. Release readiness

- [x] 11.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst`
- [x] 11.2 Main specs amended in place for every requirement this touched
- [x] 11.3 Full check loop green: `ruff format`, `ruff check --show-fixes --preview`,
      `mypy aiogram`, `pytest tests` with coverage at 100%
