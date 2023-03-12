==========================
Migration FAQ (2.x -> 3.0)
==========================

.. danger::

    This guide is still in progress.

This version introduces much many breaking changes and architectural improvements,
helping to reduce global variables count in your code, provides mechanisms useful mechanisms
to separate your code to modules or just make sharable modules via packages on the PyPi,
makes middlewares and filters more controllable and others.

On this page you can read about points that changed corresponding to last stable 2.x version.

Dispatcher
==========

- :class:`Dispatcher` class no longer accepts the `Bot` instance into the initializer,
  it should be passed to dispatcher only for starting polling or handling event from webhook.
  Also this way adds possibility to use multiple bot instances at the same time ("multibot")
- :class:`Dispatcher` now can be extended with another Dispatcher-like
  thing named :class:`Router` (:ref:`Read more » <Nested routers>`).
  With routes you can easily separate your code to multiple modules
  and maybe share this modules between projects.
- Removed the **_handler** suffix from all event handler decorators and registering methods.
  (:ref:`Read more » <Event observers>`)
- Executor entirely removed, now you can use Dispatcher directly to start polling or webhook.

Filtering events
================

- Keyword filters can no more be used, use filters explicitly. (`Read more » <https://github.com/aiogram/aiogram/issues/942>`_)
- In due to keyword filters was removed all enabled by default filters (state and content_type now is not enabled)
- Most of common filters is replaced by "magic filter". (:ref:`Read more » <magic-filters>`)
- Now by default message handler receives any content type, if you want specific one just add the filters (Magic or any other)
- State filter is not enabled by default, that's mean if you using :code:`state="*"` in v2
  then you should not pass any state filter in v3, and vice versa,
  if the state in v2 is not specified now you should specify the state.
- Added possibility to register per-router global filters, that helps to reduces
  the number of repetitions in the code and makes easily way to control
  for what each router will be used.

Bot API Methods
===============

- Now all API methods is classes with validation (via `pydantic <https://docs.pydantic.dev/>`_)
  (all API calls is also available as methods in the Bot class)
- Increased pre-defined Enums count and moved into `aiogram.enums` sub-package.
- Separated HTTP client session into container that can be reused between different
  Bot instances in the application.

Middlewares
===========

- Middlewares can now control a execution context, e.g. using context managers (:ref:`Read more » <middlewares>`)
- All contextual data now is shared between middlewares, filters and handlers to end-to-end use.
  For example now you can easily pass some data into context inside middleware and
  get it in the filters layer as the same way as in the handlers via keyword arguments.
- Added mechanism named **flags**, that helps to customize handler behavior
  in conjunction with middlewares.

Keyboard Markup
===============

- Now :class:`aiogram.types.inline_keyboard_markup.InlineKeyboardMarkup`
  and :class:`aiogram.types.reply_keyboard_markup.ReplyKeyboardMarkup` has no methods to extend it,
  instead you have to use markup builders :class:`aiogram.utils.keyboard.ReplyKeyboardBuilder`
  and :class:`aiogram.utils.keyboard.KeyboardBuilder` respectively
  (:ref:`Read more » <keyboard-builder>`)


Callbacks data
==============

- Callback data factory now is strictly typed via `pydantic <https://docs.pydantic.dev/>`_ models
  (:ref:`Read more » <callback-data-factory>`)

Finite State machine
====================

- State filter will no more added to all handlers, you will need to specify state if you want

Sending Files
=============

- From now you should wrap sending files into InputFile object before send instead of passing
  IO object directly to the API method. (:ref:`Read more » <sending-files>`)

Webhook
=======

- Simplified aiohttp web app configuration
- By default added possibility to upload files when you use reply into webhook


..
    This part of document will be removed

    .. code-block:: markdown

        ## Keyboards and filters (part 1)

        - `(Reply|Inline)KeyboardMarkup` is no longer used for building keyboards via `add`/`insert`/`row`, use `(Reply|Inline)KeyboardBuilder` and `button` instead.
        - `CallbackData` is now a base class, not a factory.
        - Integrate `[magic-filter](https://pypi.org/project/magic-filter/)` into aiogram.
            - Code for 2.x

                ```python
                from secrets import token_urlsafe

                from aiogram import Bot, Dispatcher
                from aiogram.types import (
                    CallbackQuery,
                    InlineKeyboardButton,
                    InlineKeyboardMarkup,
                    Message,
                )
                from aiogram.utils.callback_data import CallbackData

                dp = Dispatcher(Bot(TOKEN))

                vote_cb = CallbackData("vote", "action", "id", sep="_")
                votes = {}  # For demo purposes only! Use database in real code!

                @dp.message_handler(commands="start")
                async def post(message: Message) -> None:
                    vote_id = token_urlsafe(8)  # Lazy way to generate a random string
                    kb = (
                        InlineKeyboardMarkup(row_width=2)
                        .insert(InlineKeyboardButton(text="+1", callback_data=vote_cb.new(action="up", id=vote_id)))
                        .insert(InlineKeyboardButton(text="-1", callback_data=vote_cb.new(action="down", id=vote_id)))
                        .insert(InlineKeyboardButton(text="?", callback_data=vote_cb.new(action="count", id=vote_id)))
                    )
                    await message.reply("Vote on this post", reply_markup=kb)

                @dp.callback_query_handler(vote_cb.filter(action="count"))
                async def show_voters_count(query: CallbackQuery, callback_data: dict) -> None:
                    vote_id = int(callback_data["id"])
                    votes[vote_id] = votes.setdefault(vote_id, 0) + 1
                    await query.answer(votes[vote_id], cache_time=1)

                @dp.callback_query_handler(vote_cb.filter())  # all other actions
                async def vote(query: CallbackQuery, callback_data: dict) -> None:
                    if (action := callback_data["action"]) == "up":
                        d = 1
                    elif action == "down":
                        d = -1
                    else:
                        raise AssertionError(f"action action!r} is not implemented")
                    votes[int(callback_data["id"])] += d
                    await query.answer(f"{action.capitalize()}voted!")
                ```

            - Code for 3.0

                ```python
                from enum import Enum
                from secrets import token_urlsafe

                from aiogram import Dispatcher, F
                from aiogram.types import CallbackQuery, Message
                from aiogram.dispatcher.filters.callback_data import CallbackData
                from aiogram.utils.keyboard import InlineKeyboardBuilder

                dp = Dispatcher()
                votes = {}  # For demo purposes only! Use database in real code!

                class VoteAction(Enum):
                    UP = "up"
                    DOWN = "down"
                    COUNT = "count"

                class VoteCallback(CallbackData, prefix="vote", sep="_"):
                    action: VoteAction  # Yes, it also supports `Enum`s
                    id: str

                @dp.message(commands="start")
                async def post(message: Message) -> None:
                    vote_id = token_urlsafe(8)  # Lazy way to generate a random string
                    kb = (
                        InlineKeyboardBuilder()
                        .button(text="+1", callback_data=VoteCallback(action=VoteAction.UP, id=vote_id))
                        .button(text="-1", callback_data=VoteCallback(action=VoteAction.DOWN, id=vote_id))
                        .button(text="?", callback_data=VoteCallback(action=VoteAction.COUNT, id=vote_id))
                        .adjust(2)  # row_width=2
                    )
                    await message.reply("Vote on this post", reply_markup=kb.as_markup())

                # `F` is a `MagicFilter` instance, see docs for `magic-filter` for more info
                @dp.callback_query(VoteCallback.filter(F.action == VoteAction.COUNT))
                async def show_voters_count(
                    query: CallbackQuery,
                    callback_data: VoteCallback,  # Now it is the class itself, not a mysterious `dict`
                ) -> None:
                    vote_id = callback_data.id
                    votes[vote_id] = votes.setdefault(vote_id, 0) + 1
                    await query.answer(votes[vote_id], cache_time=1)

                @dp.callback_query(VoteCallback.filter())  # all other actions
                async def vote(query: CallbackQuery, callback_data: VoteCallback) -> None:
                    if callback_data.action == VoteAction.UP:
                        d = 1
                    elif callback_data.action == VoteAction.DOWN:
                        d = -1
                    else:
                        raise AssertionError(f"action {callback_data.action!r} is not implemented")
                    votes[callback_data.id] += d
                    await query.answer(f"{action.capitalize()}voted!")
                ```


        ## Code style

        - Allow the code to be split into several files in a convenient way with `Router`s.
        - Make `Dispatcher` a router with some special abilities.
        - Remove `<event>_handler` in favor of `<event>` (e.g. `dp.message()` instead of `dp.message_handler()`)
            - Code for 2.x (one of possible ways)

                ```python
                from aiogram import Bot, Dispatcher, executor
                from mybot import handlers

                dp = Dispatcher(Bot(TOKEN))

                handlers.hello.setup(dp)
                ...

                executor.start_polling(dp, ...)
                ```

                ```python
                from aiogram import Dispatcher
                from aiogram.types import Message

                # No way to use decorators :(
                async def hello(message: Message) -> None:
                    await message.reply("Hello!")

                async def goodbye(message: Message) -> None:
                    await message.reply("Bye!")

                def setup(dp: Dispatcher) -> None:
                    dp.register_message_handler(hello, commands=["hello", "hi"])
                    dp.register_message_handler(goodbye, commands=["goodbye", "bye"])
                    # This list can become huge in a time, may be inconvenient
                ```

            - Code for 3.0

                ```python
                from aiogram import Bot, Dispatcher
                from mybot import handlers

                dp = Dispatcher()

                # Any router can include a sub-router
                dp.include_router(handlers.hello.router)  # `Dispatcher` is a `Router` too
                ...

                dp.run_polling(Bot(TOKEN))  # But it's special, e.g. it can `run_polling`
                ```

                ```python
                from aiogram import Router
                from aiogram.types import Message

                router = Router()

                # Event handler decorator is an event type itself without `_handler` suffix
                @router.message(commands=["hello", "hi"])  # Yay, decorators!
                async def hello(message: Message) -> None:
                    await message.reply("Hello!")

                async def goodbye(message: Message) -> None:
                    await message.reply("Bye!")

                # If you still prefer registering handlers without decorators, use this
                router.message.register(goodbye, commands=["goodbye", "bye"])
                ```


        ## Webhooks and API methods

        - All methods are classes now.
        - Allow using Reply into webhook with polling. *Check whether it worked in 2.x*
        - Webhook setup is more flexible ~~and complicated xd~~

        ## Exceptions

        - No more specific exceptions, only by status code.
            - Code for 2.x [todo]

                ```python
                from asyncio import sleep

                from aiogram import Bot, Dispatcher
                from aiogram.dispatcher.filters import Command
                from aiogram.types import Message
                from aiogram.utils.exceptions import (
                    BadRequest,
                    BotBlocked,
                    RestartingTelegram,
                    RetryAfter,
                )

                dp = Dispatcher(Bot(TOKEN))
                chats = set()

                async def broadcaster(bot: Bot, chat: int, text: str) -> bool:
                    """Broadcasts a message and returns whether it was sent"""
                    while True:
                            try:
                                await bot.send_message(chat, text)
                            except BotBlocked:
                                chats.discard(chat)
                                log.warning("Remove chat %d because bot was blocked", chat)
                            return False
                            except RetryAfter as e:
                                log.info("Sleeping %d due to flood wait", e.retry_after)
                                await sleep(e.retry_after)
                            continue
                        except RestartingTelegram:
                            log.info("Telegram is restarting, sleeping for 1 sec")
                            await sleep(1)
                            continue
                        except BadRequest as e:
                            log.warning("Remove chat %d because of bad request", chat)
                            chats.discard(chat)
                            return False
                        else:
                            return True

                @dp.message_handler(commands="broadcast")
                async def broadcast(message: Message, command: Command.CommandObj) -> None:
                    # TODO ...
                ```

            - Code for 3.x [todo]

                ```python
                ...
                ```


        ## Filters (part 2)

        - Remove the majority of filters in favor of `MagicFilter` (aka `F`).
        - Deprecate usage of bound filters in favor of classes, functions and `F`.
        - Message handler defaults to any content type.
        - Per-router filters.

        ## Middlewares and app state

        - Rework middleware logic.
        - Pass `**kwargs` from `start_polling` to handlers and filters.
        - No more global `bot` and `message.bot`.
            - `bot["foo"]` → `dp["foo"]`.

        ## FSM

        - FSMStrategy.
        - Default to any state.
        - States are also callable filters.
        - No more `next` and `proxy`.
        - No state filtering is done by default:

            [Default state is not None · Issue #954 · aiogram/aiogram](https://github.com/aiogram/aiogram/issues/954#issuecomment-1172967490)


        ## Misc

        - No more unrelated attributes and methods in types.
            - `get_args()`
            - `get_(full_)command()`
            - …?
        - Add handler flags.
        - ???
