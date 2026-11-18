# Architecture

How `aiogram.test` is put together. For why it is built this way, see [decisions.md](decisions.md). For the rules
a change must keep, see [invariants.md](invariants.md).

## The idea

The toolkit runs the bot's real `Dispatcher` against a fake Telegram. Two seams in aiogram make this possible
without patching anything:

- `Dispatcher.feed_update(bot, update)` is where polling and webhooks hand updates to routing. The toolkit feeds
  updates there, so filters, middlewares, dependency injection, FSM and Scenes run unchanged.
- `BaseSession.make_request(bot, method)` is where every Bot API call leaves the process. The toolkit swaps in its
  own session (`FakeTelegramSession`), so shortcuts (`message.answer()`), request middlewares and error handling
  run unchanged too.

Between the two seams sits a `World`: an in-memory model of chats, users, memberships, messages and the bot's own
state. Bot calls change it, and actors read from it to build the updates they send.

## Flow of one test step

```
test ──► UserActor.send("/start")
           │  writes the user's message into ChatState, builds an Update around the same object
           ▼
         BotTestEnvironment.feed(update)
           │  adopt(): bind the update's objects to env.bot (or copy them if another env owns them)
           │  open a routing scope (RouteRecord collection)
           ▼
         Dispatcher.feed_update(bot, update)          ← real aiogram, untouched
           │  handler calls message.answer("Hi")
           ▼
         FakeTelegramSession.make_request(bot, method)
           ▼
         BotTestEnvironment.handle_call(bot, method)
           1. resolve Default(...) sentinels          (defaults.py)
           2. record the call in CallLog              (calls.py)  ← before anything can refuse it
           3. detached_copy of the method             (mounting.py)
           4. override registered with env.on(...)?   (overrides.py) → declared result / error
           5. modeled method?                         (modeling.py, @models registry)
                - refuse empty text, apply parse modes (markup.py)
                - check the bot's rights and standing  (modeling.check_bot_rights)
                - run the handler: mutate World, return the stored object
                - count a successful send for flood control (flood.py)
           6. otherwise synthesize a schema-valid result from __returning__ (synthesis.py)
           ▼
         mount(result, bot)  → handler gets world objects bound to the bot
           ▼
test ◄── asserts on bot_chat.messages, env.calls, env.last_route, …
```

Refusals come back as the `TelegramBadRequest` / `TelegramForbiddenError` / `TelegramRetryAfter` that the real API
would raise (`ApiRejection` → `raise_api_error`). A gap in the test's own setup, such as a chat the blueprint never
declared, raises `WorldLookupError` instead. The bot cannot catch that by mistake.

## Modules

| Module | Role |
|---|---|
| `__init__.py` | Public exports. Does not import pytest. |
| `plugin.py` | The opt-in pytest plugin: the `bot_*` fixtures, the `bot_env_*` knobs, the post-test `assert_updates_handled` hook, and `pytest_assertrepr_compare` for world and call objects. |
| `environment.py` | `BotTestEnvironment`: owns the `World`, `Bot`, `Dispatcher`, `CallLog`, `OverrideRegistry` and clock. Holds `feed`/`adopt`, `handle_call`, the waits (`wait_for`, `wait_for_message_in`), background-task tracking and draining (the loop task factory), and routing diagnostics (`RouteRecord`, scopes, `last_route`/`routes`/`all_routes`/`assert_handled_by`). |
| `blueprint.py` | `Blueprint` and the `*Spec` declarations. Immutable descriptions that every test materializes into a fresh `World`. `default_blueprint()` is one user in a private chat. |
| `world.py` | The world's state: `World`, `ChatRegistry`, `ChatState`, `UserState`, `MemberState`, `TopicState`, `PollState`, `InviteLinkState`, `StarLedger`, `BotProfileState`, …. Also rights and permission helpers, the world clock, and `WorldLookupError`. |
| `actors.py` | `UserActor`: one trigger per `Update` variant (`send`, `click`, `reply`, `follow_deep_link`, `join`, `promote`, `pay`, `widget_query`, …). `Withheld` is returned when the update does not reach the bot. |
| `modeling.py` | What each Bot API method does to the world. Handlers are registered with `@models(Method, sends=...)` and looked up by `find_handler`. Holds the rights checks (`check_bot_rights`, `RightRule`). |
| `synthesis.py` | Builds a schema-valid result from a method's `__returning__` annotation, using pydantic field metadata only. Values are seeded from the world (`SynthesisContext`). |
| `overrides.py` | `env.on(Method, **filters)`: `OverrideBuilder` / `OverrideRegistry` / `MethodMatcher`. Also the "blocked by user" recipe (`block_chat`, `BLOCKED_METHODS`) and never-fired reporting. |
| `rejections.py` | Every rejection the toolkit can raise, declared once: code, description, source. Supports perturbing the descriptions, so bots that match on error text get caught. |
| `errors.py` | `ApiRejection`, `NoFileContentError`, `WaitTimeoutError`, `BackgroundTaskError`, `DrainedTaskError`, `raise_api_error`. |
| `mounting.py` | The boundary between world objects and code under test: `mount`, `detach`, `detached_copy`, `owned_or_copied`, `bindables`. |
| `markup.py` | Ports of the Bot API's HTML / MarkdownV2 / Markdown parsers, plus `bot_command` entities for user text. |
| `rich.py` | Converts `InputRich*` blocks to the stored `Rich*` blocks by reflection. |
| `flood.py` | Optional per-chat flood limits (`RateLimits`), counted on successful modeled sends. |
| `session.py` | `FakeTelegramSession`: forwards to `handle_call` and serves downloads from `World.files`. |
| `calls.py` | `CallLog`. |
| `defaults.py` | `resolve_defaults`: replaces `Default(...)` sentinels the way serialization does. |
| `waiting.py` | `poll_until`, the polling loop behind every wait. It is bounded by its deadline and evaluates a predicate once more after the last sleep. |
| `routing.py` | `detach_router`: lets a module-level router be included again. 3.x only. |

## Where to add things

- **A new Bot API method that changes state:** add a `@models` handler in `modeling.py` and the state it needs in
  `world.py`. Add a test that drives it through a handler. If no handler exists, the method is record-only:
  synthesis answers it, and nothing else is needed.
- **A new `Update` variant:** add a trigger on `UserActor` and an entry in `TRIGGERS` in
  `tests/test_testing/test_triggers.py`. The guard there fails until both exist.
- **A new refusal:** declare it in `rejections.py`, with its source if the Bot API documents the wording, and raise
  it through `ApiRejection`.
- **A new fixture knob:** add a `bot_env_*` fixture in `plugin.py`, a matching `BotTestEnvironment` argument, and a
  line in the docs' fixture list.

## Relation to 4.x

The 4.0 plans (`v4/plans/H-testing-observability/`, H-10..H-20) keep the user-facing names. They rewrite the parts
that rely on 3.x internals:

- `synthesis.py` and the `model_fields` / `ContentType` reflection become tables generated from the IR (H-11, H-12);
- `mounting.py` becomes construction already bound to the bot (H-13);
- the task-factory tracking and `detach_router` become delivery through the Runner (H-14);
- the routing middleware becomes the trace hook (H-15);
- the modeled / synthesized marks become visible (H-16).

The frozen user-facing surface is listed at the top of `docs/dispatcher/testing.rst`.
