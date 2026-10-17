.. |Bot| replace:: :class:`~aiogram.client.bot.Bot`
.. |Dispatcher| replace:: :class:`~aiogram.dispatcher.dispatcher.Dispatcher`
.. |Router| replace:: :class:`~aiogram.dispatcher.router.Router`

==========================
Migration FAQ (2.x -> 3.x)
==========================

This version introduces numerous breaking changes and architectural improvements.
It helps reduce the count of global variables in your code, provides useful mechanisms
to modularize your code, and enables the creation of shareable modules via packages on PyPI.
It also makes middlewares and filters more controllable, among other improvements.

On this page, you can read about the changes made in relation to the last stable 2.x version.

.. danger::

    Most breaking changes on this page fall into two groups:
    code that **fails loudly** right after the upgrade (import errors, removed methods)
    and code that **fails silently** — it imports and runs, but misbehaves only on
    specific updates or under specific conditions.
    The silent group is marked with warnings across this page; pay extra attention to it.

    Renames are cheap to migrate: imports and linters catch them within an hour.
    The dangerous group is **changed defaults and implicit contracts** — the state
    and content-type filters implied by v2 handlers, :code:`parse_mode=None`,
    model equality, optional lists becoming :code:`None` — which compile, pass
    smoke tests, and break only on live behavior.

.. note::

    Feel free to contribute to this page, if you find something that is not mentioned here.


Dependencies
============

- The dependencies required for :code:`i18n` are no longer part of the default package.
  If your application uses translation functionality, be sure to add an optional dependency:

  :code:`pip install aiogram[i18n]`

  Note that the i18n API itself has also been changed, see :ref:`i18n migration <migration-i18n>` below.

- aiogram 3.x requires a much newer aiohttp than v2 did
  (:code:`aiohttp >= 3.9` at the time of writing — check aiogram's project metadata
  for the current bounds).
  If your project uses aiohttp directly (for example, for a webhook web application),
  check your own code against the aiohttp changelog: arguments that were deprecated
  in older aiohttp versions have been removed (e.g. the :code:`loop=` argument of
  :code:`aiohttp.web.Application`).

- Redis storage is now based on the `redis <https://pypi.org/project/redis/>`_ package
  (with asyncio support) instead of :code:`aioredis`.

- aiogram 3.x is built on `pydantic <https://docs.pydantic.dev/>`_ v2. If your project
  used pydantic v1 for its **own** models (settings, database schemas), upgrading
  aiogram is often the moment pydantic v2 first enters the project — and some v1
  patterns break **silently**: for example, :code:`Field(..., env="REDIS_URL")` is
  ignored by pydantic v2 (:code:`BaseSettings` moved to the separate
  :code:`pydantic-settings` package), so a config quietly stops reading environment
  variables. Check your own models against the
  `pydantic v1 -> v2 migration guide <https://docs.pydantic.dev/latest/migration/>`_.

- Recent aiogram releases pin an **upper** Python bound as well (e.g.
  :code:`>=3.10,<3.15` — check the current project metadata). With Poetry, a caret
  constraint like :code:`python = "^3.11"` (which means :code:`<4.0`) then fails to
  lock; use an explicitly bounded range such as :code:`>=3.11,<3.15`.


Bot
===

Default bot properties (parse_mode and others)
----------------------------------------------

In v2 the global parse mode was configured directly on the |Bot| instance
(:code:`Bot(token, parse_mode="HTML")`). In v3 all per-bot defaults are grouped into
:class:`~aiogram.client.default.DefaultBotProperties`:

.. code-block:: python

    # Version 2.x
    bot = Bot(token, parse_mode="HTML")

.. code-block:: python

    # Version 3.x
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

:class:`~aiogram.client.default.DefaultBotProperties` also covers other defaults:
:code:`disable_notification`, :code:`protect_content`, :code:`link_preview_is_disabled`
and other link preview options, etc.

.. note::

    In aiogram 3.0 - 3.6 the :code:`Bot(parse_mode=...)` form was still accepted;
    it was removed in 3.7 in favor of :code:`DefaultBotProperties`.
    If you migrate straight to a recent 3.x release, use :code:`DefaultBotProperties` only.

.. warning::

    :code:`parse_mode=None` in an API call now means the **opposite** of v2.
    In v2, method arguments equal to :code:`None` were dropped from the payload and
    the bot-level default was applied (:code:`payload.setdefault("parse_mode",
    self.parse_mode)`), so :code:`parse_mode=None` meant "use the bot default".
    In v3 the "use the default" marker is the :code:`Default("parse_mode")` sentinel,
    and an **explicit** :code:`None` overrides it — i.e. disables formatting entirely.

    Any wrapper that forwards the parameter, like
    :code:`async def send(..., parse_mode=None): await message.answer(text, parse_mode=parse_mode)`,
    compiles and silently shows users raw :code:`<b>` tags. Make the wrapper default
    to the sentinel instead of :code:`None`:

    .. code-block:: python

        from aiogram.client.default import Default

        async def send(..., parse_mode: str | Default | None = Default("parse_mode")):
            await message.answer(text, parse_mode=parse_mode)

:code:`bot.me` is now a method
------------------------------

In v2 :code:`me` was a property (:code:`me = await bot.me`), in v3 it is a method
(with cached result):

.. code-block:: python

    # Version 2.x
    me = await bot.me

    # Version 3.x
    me = await bot.me()

.. warning::

    This is a silent breakage: :code:`await bot.me` in v3 fails only at runtime
    (awaiting a method object), so grep your project for :code:`.me` usages.

Bot is no longer a context storage
----------------------------------

In v2 both |Bot| and |Dispatcher| could be used as dictionaries to store arbitrary
runtime data (:code:`bot["db"] = ...`, documented as a feature). In v3:

- |Dispatcher| still supports this via
  :code:`dispatcher.workflow_data` (:code:`dp["key"] = value` still works),
  and all values stored there are automatically injected into handlers,
  filters, and middlewares as keyword arguments by name.
- |Bot| is no longer a data storage of any kind.

.. code-block:: python

    # Version 2.x
    bot["db"] = db
    dp["config"] = config

    # Version 3.x
    dp["db"] = db          # or Dispatcher(db=db, config=config)
    dp["config"] = config

    @router.message(Command("info"))
    async def handler(message: Message, db: Database, config: Config) -> None:
        # values from workflow_data are injected by argument name
        ...

If you stored data on the |Bot| instance because multiple bots shared one dispatcher,
move that data to a middleware or derive it from the :code:`bot` argument
(e.g. keyed by :code:`bot.id`).


Dispatcher
==========

- The |Dispatcher| class no longer accepts a |Bot| instance in its initializer.
  Instead, the |Bot| instance should be passed to the dispatcher only for starting polling
  or handling events from webhooks. This approach also allows for the use of multiple bot
  instances simultaneously ("multibot").
- |Dispatcher| now can be extended with another Dispatcher-like thing named |Router|.
  With routes, you can easily modularize your code and potentially share these modules between projects.
  (:ref:`Read more » <Nested routers>`.)
- Removed the **_handler** suffix from all event handler decorators and registering methods.
  (:ref:`Read more » <Event observers>`)
- The :code:`Executor` has been entirely removed; you can now use the |Dispatcher| directly to start poll the API or handle webhooks from it.
- Throttling (:code:`dp.throttle`, :code:`Throttled`, the :code:`rate_limit` pattern) has been
  completely removed; see the :ref:`Throttling <migration-throttling>` section for the
  replacement recipe based on middlewares and flags.
- Removed global context variables from the API types, |Bot| and |Dispatcher| object.
  From now on, if you want to access the current bot instance within handlers or filters,
  you should accept the argument :code:`bot: Bot` and use it instead of :code:`Bot.get_current()`.
  In middlewares, it can be accessed via :code:`data["bot"]`.
- To skip pending updates, you should now call the :class:`~aiogram.methods.delete_webhook.DeleteWebhook` method directly, rather than passing :code:`skip_updates=True` to the start polling method.
- To feed updates to the |Dispatcher|, instead of method :code:`process_update()`,
  you should use method :meth:`~aiogram.dispatcher.dispatcher.Dispatcher.feed_update`.
  (:ref:`Read more » <Handling updates>`)

Background handler execution (:code:`run_task`) is removed
----------------------------------------------------------

The v2 options :code:`Dispatcher(run_tasks_by_default=True)` and
:code:`@dp.message_handler(run_task=True)`, which executed handlers in background tasks,
were removed without a direct equivalent.

In v3, each **update** is already processed in its own task during polling
(:code:`start_polling(handle_as_tasks=True)` is the default), so slow handlers do not
block other users. If you still need fire-and-forget behavior inside a handler,
schedule the work explicitly:

.. code-block:: python

    import asyncio

    background_tasks = set()

    @router.message(Command("slow"))
    async def handler(message: Message) -> None:
        task = asyncio.create_task(do_slow_work(message.chat.id))
        background_tasks.add(task)  # keep a reference to avoid premature garbage collection
        task.add_done_callback(background_tasks.discard)

Note that an exception raised inside a detached task never reaches the aiogram error
handlers — the update is already considered processed by then. Keep a reference to the
task and handle (or at least log) errors inside it yourself.

:code:`AllowedUpdates` helper is removed
----------------------------------------

The v2 helper :code:`aiogram.types.AllowedUpdates` no longer exists.
In v3 pass plain strings or :class:`aiogram.enums.update_type.UpdateType` members,
or resolve the list from your registered handlers via
:meth:`~aiogram.dispatcher.router.Router.resolve_used_update_types`:

.. code-block:: python

    # Version 2.x
    executor.start_polling(dp, allowed_updates=types.AllowedUpdates.MESSAGE)

.. code-block:: python

    # Version 3.x
    from aiogram.enums import UpdateType

    await dp.start_polling(bot, allowed_updates=[UpdateType.MESSAGE])
    # or let aiogram compute it from your handlers:
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

.. warning::

    When :code:`allowed_updates` is not passed to :code:`start_polling`, aiogram 3
    automatically requests **only the update types for which you have handlers**
    (it calls :code:`resolve_used_update_types()` for you). This differs from v2,
    where the bot received the server-default set of updates. If some of your updates
    are consumed only by middlewares or outside the dispatcher, pass
    :code:`allowed_updates` explicitly.


Filtering events
================

- Keyword filters can no longer be used; use filters explicitly. (`Read more » <https://github.com/aiogram/aiogram/issues/942>`_)
- Due to the removal of keyword filters, all previously enabled-by-default filters
  (such as state and content_type) are now disabled.
  You must specify them explicitly if you wish to use them.
  For example instead of using :code:`@dp.message_handler(content_types=ContentType.PHOTO)`
  you should use :code:`@router.message(F.photo)`
- Most common filters have been replaced with the "magic filter." (:ref:`Read more » <magic-filters>`)
- Added the possibility to register global filters for each router, which helps to reduce code
  repetition and provides an easier way to control the purpose of each router.

.. warning::

    **A bare v2 handler had two implicit filters; a bare v3 handler has none.**

    :code:`@dp.message_handler()` without arguments implicitly meant
    :code:`content_types=ContentType.TEXT` **and** :code:`state=None`
    (outside of any FSM state). :code:`@router.message()` means neither —
    it receives every content type in every state. Consequences of a
    straight-across migration:

    - stickers and photos land in "text" handlers, and :code:`message.text.lower()`
      raises :code:`AttributeError: 'NoneType' object has no attribute 'lower'`
      on the first non-text message;
    - handlers fire in the middle of FSM dialogs where v2 silently skipped them
      (see `Default state filter behavior is inverted`_);
    - :code:`Command()` now also matches commands in **media captions** — in v2 the
      implicit :code:`TEXT` filter masked that.

    Add the content filter explicitly:

    .. code-block:: python

        # Version 2.x
        @dp.message_handler()
        async def handler(message: types.Message):
            print(message.text.lower())

    .. code-block:: python

        # Version 3.x
        @router.message(F.text)
        async def handler(message: Message) -> None:
            print(message.text.lower())

    Use the matching magic filter for other content types
    (:code:`F.photo`, :code:`F.document`, :code:`F.sticker`, ...), or keep the handler
    unfiltered on purpose and guard every field access.

The :code:`chat_type` filter
----------------------------

The commonly used v2 keyword filter :code:`chat_type=` should be replaced with a magic
filter. Note that **the path to the chat differs between event types**:

.. code-block:: python

    # Version 2.x
    @dp.message_handler(chat_type=types.ChatType.PRIVATE)
    @dp.callback_query_handler(chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])

.. code-block:: python

    # Version 3.x
    from aiogram import F
    from aiogram.enums import ChatType

    @router.message(F.chat.type == ChatType.PRIVATE)
    @router.callback_query(F.message.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))

.. warning::

    For a message the chat is :code:`F.chat`, but for a callback query the chat lives
    on the attached message: :code:`F.message.chat`. A copied-over
    :code:`F.chat.type` filter on a callback query handler compiles and **simply
    never matches** — the handler goes silently dead.

The :code:`Text` filter
-----------------------

The v2 :code:`Text` filter has no equivalent in v3: it was dropped during the 3.0 beta
cycle (in 3.0.0b8), before the first stable 3.0 release, so it is not available in any
stable 3.x version. Use the magic filter:

.. code-block:: python

    # Version 2.x
    @dp.message_handler(text="hello")
    @dp.message_handler(text_startswith="foo")

.. code-block:: python

    # Version 3.x
    @router.message(F.text == "hello")
    @router.message(F.text.startswith("foo"))
    # also useful: F.text.in_({...}), F.text.contains(...),
    # case-insensitive: F.text.casefold() == "hello"

.. note::

    Don't confuse the removed filter with :class:`aiogram.utils.formatting.Text` —
    that one is a text formatting tool, not a filter.

Command arguments (:code:`message.get_args`)
--------------------------------------------

The v2 method :code:`Message.get_args()` is removed. The :class:`~aiogram.filters.command.Command`
filter now passes a :class:`~aiogram.filters.command.CommandObject` into the handler:

.. code-block:: python

    # Version 2.x
    @dp.message_handler(commands=["start"])
    async def handler(message: types.Message):
        args = message.get_args()  # "" if no args

.. code-block:: python

    # Version 3.x
    from aiogram.filters import Command, CommandObject

    @router.message(Command("start"))
    async def handler(message: Message, command: CommandObject) -> None:
        args = command.args  # None if no args

Note that :code:`command.args` is :code:`None` (not an empty string) when the command
has no arguments.

Other removed :code:`Message` helpers
-------------------------------------

:code:`Message.is_command()`, :code:`Message.get_command()` and
:code:`Message.is_forward()` were removed **without replacement**. Inside the
dispatcher, use the :class:`~aiogram.filters.command.Command` filter and
:class:`~aiogram.filters.command.CommandObject` instead. If you inspect updates
*outside* the dispatcher (custom routing, raw update processing), reimplement the
checks manually:

.. code-block:: python

    def is_command(message: Message) -> bool:
        # v2-parity: media captions count too, and no entity is required
        text = message.text or message.caption
        return bool(text and text.startswith("/"))

    def is_forward(message: Message) -> bool:
        return message.forward_origin is not None

Mind the exact v2 semantics when writing the replacement:

- v2 :code:`is_command()` was literally "text **or caption** starts with :code:`/`",
  and no :code:`bot_command` entity was required. A stricter entity-based check
  narrows behavior (captions stop counting, and commands that Telegram does not mark
  with an entity — e.g. non-ASCII ones like :code:`/пинг` — stop matching); aiogram's
  own :class:`~aiogram.filters.command.Command` filter also parses text/caption
  rather than entities.
- v2 :code:`is_forward()` was :code:`bool(message.forward_date)`. The field still
  exists on the v3 model but is deprecated and never populated since Bot API 7.0,
  so that check silently becomes always-false — use
  :code:`message.forward_origin is not None`
  (see `Forwarded messages: forward_from is dead`_).

Default state filter behavior is inverted
-----------------------------------------

.. warning::

    This is one of the most dangerous silent changes in v3.

    - In v2 a handler **without** a state filter ran only in the default (no) state;
      to run in any state you had to pass :code:`state="*"`.
    - In v3 a handler **without** a :code:`StateFilter`
      (:code:`from aiogram.filters import StateFilter`) runs in **any** state.

    After a naive migration, handlers start to trigger in situations where they were
    silently skipped before — e.g. a menu handler now fires in the middle of an FSM dialog.

    Migration rules:

    - v2 :code:`state="*"` -> v3: no state filter at all.
    - v2 without state -> v3: :code:`StateFilter(None)` if you want to keep the old behavior.
    - v2 :code:`state=MyGroup.my_state` -> v3: :code:`StateFilter(MyGroup.my_state)`
      (or pass the state directly as a filter: :code:`@router.message(MyGroup.my_state)`).


Bot API
=======

- All API methods are now classes with validation, implemented via
  `pydantic <https://docs.pydantic.dev/>`_.
  These API calls are also available as methods in the Bot class.
- More pre-defined Enums have been added and moved to the `aiogram.enums` sub-package.
  For example, the chat type enum is now :class:`aiogram.enums.chat_type.ChatType`
  instead of :code:`aiogram.types.chat.ChatType`.
- The HTTP client session has been separated into a container that can be reused
  across different Bot instances within the application.
- API Exceptions are no longer classified by specific messages,
  as Telegram has no documented error codes.
  However, all errors are classified by HTTP status codes, and for each method,
  only one type of error can be associated with a given code.
  Therefore, in most cases, you should check only the error type (by status code)
  without inspecting the error message. More details can be found in the
  :ref:`exceptions section » <error-types>`.

Renamed methods
---------------

v2 kept some pre-Bot API 5.3 method names that are gone in v3:

- :code:`bot.kick_chat_member` -> :code:`bot.ban_chat_member`
  (:class:`aiogram.methods.ban_chat_member.BanChatMember`)
- :code:`bot.get_chat_members_count` -> :code:`bot.get_chat_member_count`
  (:class:`aiogram.methods.get_chat_member_count.GetChatMemberCount`)
- :code:`bot.set_sticker_set_thumb` -> :code:`bot.set_sticker_set_thumbnail`
  (:class:`aiogram.methods.set_sticker_set_thumbnail.SetStickerSetThumbnail`)
- :code:`bot.close_bot` -> :code:`bot.close`
  (:class:`aiogram.methods.close.Close`, the Bot API :code:`close` method;
  to close the HTTP client session, use :code:`await bot.session.close()`)
- :code:`bot.download_file_by_id` -> :meth:`~aiogram.client.bot.Bot.download`,
  which accepts both a file id and a :class:`~aiogram.types.file.File`-like object

All other methods follow the current Bot API names — when in doubt, check the method
list in the API reference rather than assuming the v2 name still exists.

Renames and removals inside Telegram types
------------------------------------------

The same applies to shortcuts and fields of the types themselves:

- :code:`chat.kick(...)` -> :meth:`aiogram.types.chat.Chat.ban`
  (:meth:`aiogram.types.chat.Chat.unban` kept its name).
- :code:`ChatPermissions.can_send_media_messages` no longer exists: Bot API 6.5 split it
  into the granular :code:`can_send_audios`, :code:`can_send_documents`,
  :code:`can_send_photos`, :code:`can_send_videos`, :code:`can_send_video_notes` and
  :code:`can_send_voice_notes` flags.

.. warning::

    Telegram types in v3 accept extra fields, so
    :code:`ChatPermissions(can_send_media_messages=True)` does **not** raise a validation
    error. The unknown field is sent to Telegram, ignored there, and the permissions you
    meant to grant are silently not applied. Replace it with the granular flags:

    .. code-block:: python

        # Version 2.x
        permissions = types.ChatPermissions(can_send_media_messages=True)

    .. code-block:: python

        # Version 3.x
        permissions = ChatPermissions(
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
        )

Constructors of types and methods are keyword-only
--------------------------------------------------

All Telegram types and API methods are `pydantic <https://docs.pydantic.dev/>`_ models
now, so positional arguments are not accepted:

.. code-block:: python

    # Version 2.x
    button = InlineKeyboardButton("Press me", callback_data="click")
    command = BotCommand("help", "Show help")

.. code-block:: python

    # Version 3.x
    button = InlineKeyboardButton(text="Press me", callback_data="click")
    command = BotCommand(command="help", description="Show help")

Positional construction fails with a validation error at runtime, so this cannot be
caught by import checks — grep for positional usages of Telegram types while migrating.

Positional arguments of API calls now bind to different parameters
-------------------------------------------------------------------

.. warning::

    This is the quiet counterpart of the rule above. **Calls** of Bot API methods and
    of type shortcuts still accept positional arguments — and that is exactly the
    problem. New Bot API parameters were inserted into the middle of existing
    signatures, so v2-era positional calls compile, but the values land in the wrong
    parameters:

    - The second parameter of :code:`bot.edit_message_text()` is now
      :code:`business_connection_id` (it was :code:`chat_id` in v2), so
      :code:`bot.edit_message_text(text, chat_id, message_id)` misbinds every
      argument after the first.
    - The second parameter of :meth:`aiogram.types.message.Message.answer` is now
      :code:`direct_messages_topic_id` (it was :code:`parse_mode` in v2), so
      :code:`message.answer(text, parse_mode)` passes the parse mode as a topic id.

    How this fails depends on the values, and neither way is caught before the code
    path actually runs:

    - **Type-incompatible** bindings (an :code:`int` chat id into the
      :code:`str | None` business connection id, :code:`"HTML"` into an
      :code:`int | None` topic id) raise :code:`ValidationError` — loud, but only at
      runtime, on the affected call.
    - **Type-compatible** bindings pass silently: an :code:`"@username"` chat id is a
      perfectly valid :code:`str` for :code:`business_connection_id`, and a wrapper
      forwarding :code:`parse_mode=None` binds :code:`direct_messages_topic_id=None`
      — the message is sent, just with formatting silently dropped.

    Pass **all** Bot API method arguments as keywords, and audit every positional call
    while migrating:

    .. code-block:: python

        # Version 2.x
        await bot.edit_message_text("New text", chat_id, message_id)
        await message.answer("<b>Hi</b>", "HTML")

    .. code-block:: python

        # Version 3.x
        await bot.edit_message_text(text="New text", chat_id=chat_id, message_id=message_id)
        await message.answer(text="<b>Hi</b>", parse_mode="HTML")


Telegram objects behavior
=========================

Incoming objects are immutable (frozen)
---------------------------------------

Telegram types in v3 are pydantic models, and the types you **receive** from Telegram
are frozen: :code:`Message`, :code:`CallbackQuery`, :code:`User`, :code:`Chat` and every
other subclass of :code:`aiogram.types.base.TelegramObject`. Any code that mutated such
objects in-place (most commonly tests) must be updated:

.. code-block:: python

    # Version 2.x
    message.text = "edited"

.. code-block:: python

    # Version 3.x
    new_message = message.model_copy(update={"text": "edited"})

The "input" types you build yourself and **send** to Telegram remain mutable — they
inherit :code:`aiogram.types.base.MutableTelegramObject` (:code:`frozen=False`):
:class:`~aiogram.types.inline_keyboard_button.InlineKeyboardButton`,
:class:`~aiogram.types.keyboard_button.KeyboardButton`,
the reply markup types,
:class:`~aiogram.types.bot_command.BotCommand`,
:class:`~aiogram.types.message_entity.MessageEntity`,
:class:`~aiogram.types.chat_permissions.ChatPermissions`,
the :code:`InputMedia*` family and others. Assigning to their fields still works.

Optional list fields are :code:`None`, not :code:`[]`
-----------------------------------------------------

.. warning::

    In v2, optional array fields defaulted to empty lists. In v3 they are
    :code:`None` when absent, matching the Bot API. This is not specific to
    :class:`~aiogram.types.message.Message` — it holds for **every** optional array
    field on **every** type, and there are dozens of them across the API.

    Code like :code:`for entity in message.entities:` passes review and works on
    most messages, then raises :code:`TypeError` on the first message without
    entities. The same applies to **API responses**, not only incoming updates:
    e.g. :code:`WebhookInfo.allowed_updates` is :code:`None` when unrestricted, so
    :code:`set(webhook_info.allowed_updates)` crashes right at startup.
    Always default the value:

    .. code-block:: python

        for entity in message.entities or []:
            ...

        allowed = set(webhook_info.allowed_updates or [])

Unix timestamps became :code:`datetime`
---------------------------------------

.. warning::

    v2 handled date fields inconsistently, per field. Some were parsed into
    :code:`datetime` (:code:`Message.date`, :code:`Message.edit_date`,
    :code:`ChatMember.until_date` were declared as :code:`fields.DateTimeField()`),
    others stayed raw Unix integers (:code:`WebhookInfo.last_error_date`,
    :code:`PassportFile.file_date` were plain :code:`fields.Field()` typed as
    :code:`base.Integer`). In :code:`WebhookInfo` the two kinds sat next to each
    other: :code:`last_error_date` was an :code:`int`, while
    :code:`last_synchronization_error_date` right below it was a
    :code:`datetime`.

    In v3 **every** date field uses the same annotated type,
    :code:`aiogram.types.custom.DateTime`, and pydantic parses the incoming Unix
    timestamp into a timezone-**aware** :code:`datetime` in UTC
    (:code:`message.date.tzinfo` is UTC). Serialization back to the Bot API converts
    it to an :code:`int` again, so you never build timestamps by hand.

    Every v2-era manual conversion therefore breaks with a :code:`TypeError` (the
    exact message depends on the Python version), and only when that line actually
    runs:

    .. code-block:: python

        # Version 2.x
        last_error = datetime.utcfromtimestamp(webhook_info.last_error_date)

    .. code-block:: python

        # Version 3.x — the field is already a datetime
        last_error = webhook_info.last_error_date

        # ...and converting back is explicit:
        timestamp = int(message.date.timestamp())

    Watch for the mirror-image trap: since the values are timezone-aware,
    comparing one with a naive :code:`datetime` raises
    :code:`TypeError: can't compare offset-naive and offset-aware datetimes`.
    Use an aware value on the other side of the comparison — e.g.
    :code:`datetime.now(timezone.utc)` instead of :code:`datetime.utcnow()`.

Objects are compared by value, not by id
-----------------------------------------

.. warning::

    This is a silent breakage with no error message at all.

    In v2, :code:`User.__hash__` returned :code:`self.id` and
    :code:`TelegramObject.__eq__` compared the class plus that hash, so two
    :code:`User` objects describing the same person were **equal regardless of which
    fields were filled in**.

    In v3 there is no custom :code:`__eq__` / :code:`__hash__`: pydantic compares all
    fields, and frozen models hash over the field values. Different API responses fill
    in different subsets of fields — the :code:`from_user` of an update, an entry of
    :code:`get_chat_administrators()` and the result of :code:`get_me()` are all
    different objects for the same user — so comparisons that used to match now
    silently stop matching:

    .. code-block:: python

        # Version 2.x — compared by user id
        if user == await bot.me:
            ...
        admin_users = [m.user for m in await bot.get_chat_administrators(chat_id)]
        if user in admin_users:  # worked in v2: Users matched by id
            ...

    .. code-block:: python

        # Version 3.x — compare ids explicitly
        me = await bot.me()
        if user.id == me.id:
            ...

        admins = await bot.get_chat_administrators(chat_id)
        if user.id in {admin.user.id for admin in admins}:
            ...

    The same applies to deduplication: :code:`set[User]` and
    :code:`dict[User, ...]` no longer collapse duplicates of the same user — build the
    set over :code:`user.id` instead.

The :code:`.bot` attribute and shortcut methods
-----------------------------------------------

In v2 shortcuts like :code:`message.answer(...)` resolved the bot instance from a global
context. In v3 the bot instance is attached to every object **during deserialization of
an update**, through the pydantic validation context.

Objects received in handlers work as before: :code:`await message.answer(...)` is fine.

.. warning::

    Objects you create manually (or deserialize yourself) have :code:`bot=None`,
    and their shortcut methods fail at call time. Bind the bot explicitly:

    .. code-block:: python

        message = Message.model_validate(data, context={"bot": bot})
        # or for an existing object:
        message = message.as_(bot)

    For background tasks and code far from handlers, pass the :code:`bot` instance
    explicitly instead of relying on shortcuts of stored objects.

Forwarded messages: :code:`forward_from` is dead
------------------------------------------------

.. warning::

    The v2-era fields :code:`forward_date`, :code:`forward_from`,
    :code:`forward_from_chat`, :code:`forward_from_message_id` still exist on
    :class:`~aiogram.types.message.Message`
    (deprecated), but since Bot API 7.0 Telegram **no longer sends them** — so migrated
    code that reads them compiles and silently sees :code:`None`.
    Use :attr:`~aiogram.types.message.Message.forward_origin` instead:

    .. code-block:: python

        from aiogram.types import MessageOriginUser

        if isinstance(message.forward_origin, MessageOriginUser):
            original_sender = message.forward_origin.sender_user

Note that this cuts both ways: in v2 these checks had been silently returning
:code:`False`/:code:`None` since Bot API 7.0, disabling every code branch behind
them — and an honest migration to :code:`forward_origin` **resurrects those
branches**, a production behavior change no linter or test will flag. Before
migrating, audit which v2 field checks (:code:`forward_*`, :code:`via_bot`, anything
removed by newer Bot API versions) are already always false on your real traffic:
each one is a branch that will either come back to life or should be consciously
removed.

:code:`CallbackQuery.message` can be inaccessible
-------------------------------------------------

.. warning::

    In v2, :code:`callback_query.message` was a regular :code:`Message` (or
    :code:`None`), and pressing a button attached to a message older than 48 hours
    produced a :code:`MESSAGE_ID_INVALID` API error that your error handlers caught.

    In v3 the field is :code:`Message | InaccessibleMessage | None`. For old or
    deleted messages Telegram sends :class:`~aiogram.types.inaccessible_message.InaccessibleMessage`,
    which carries only :code:`chat`/:code:`message_id`/:code:`date` (no message
    content fields at all) and has no **editing or deleting** shortcuts
    (:code:`edit_text`, :code:`edit_reply_markup`, :code:`edit_caption`,
    :code:`delete`, :code:`forward`, :code:`pin`, …) —
    :code:`callback_query.message.edit_text(...)` raises
    :code:`AttributeError` in Python before any API call is made, so the whole
    v2-era "expired button" handling silently stops working.
    (:code:`answer_*`/:code:`reply_*` send shortcuts *do* exist on
    :code:`InaccessibleMessage` since aiogram 3.13.) Check the type first:

    .. code-block:: python

        from aiogram.types import Message

        if isinstance(callback_query.message, Message):
            await callback_query.message.edit_text("...")
        else:  # InaccessibleMessage or None
            await callback_query.answer("This button has expired", show_alert=True)

:code:`repr()` of objects is much larger now
--------------------------------------------

In v2, :code:`repr(message)` was compact; in v3, pydantic renders **every** field,
including the ~150 :code:`None`-valued optional ones. Log statements like
:code:`log.debug("Processing %r", message)` multiply log volume by orders of
magnitude after migration — on busy bots this has a real storage/latency cost.
Log selected fields (e.g. :code:`message.message_id`, :code:`message.chat.id`)
instead of whole objects on hot paths.



Telegram objects transformation (to dict, to json, from json)
-------------------------------------------------------------

- Methods :code:`TelegramObject.to_object()`, :code:`TelegramObject.as_json()` and
  :code:`TelegramObject.to_python()` have been removed due to the use of
  `pydantic <https://docs.pydantic.dev/>`_ models.
- :code:`TelegramObject.to_object()` should be replaced by :code:`TelegramObject.model_validate()`
  (`Read more <https://docs.pydantic.dev/2.7/api/base_model/#pydantic.BaseModel.model_validate>`_)
- :code:`<TelegramObject>.as_json()` should be replaced by
  :code:`json.dumps(deserialize_telegram_object_to_python(<TelegramObject>))`
- :code:`<TelegramObject>.to_python()` should be replaced by
  :func:`aiogram.utils.serialization.deserialize_telegram_object_to_python`

.. warning::

    The *obvious* pydantic replacement — bare :code:`model_dump()` — is **not**
    equivalent to v2 :code:`to_python()` and silently changes the data shape:
    it includes every unset optional field as :code:`None` (dozens of keys even for
    small objects, ~150 for a :class:`~aiogram.types.message.Message`) and returns
    :code:`datetime`/enum values as Python objects rather than JSON primitives.
    Code that dumps objects into MongoDB or an external API gets bloated documents
    and a different wire format without a single error — e.g. a Mongo
    :code:`$set` built from :code:`model_dump()` overwrites previously stored
    values with :code:`None`. Use
    :func:`~aiogram.utils.serialization.deserialize_telegram_object_to_python`,
    or at least :code:`model_dump(mode="json", exclude_none=True)`.

.. code-block:: python

    # Version 2.x
    message_dict = message.to_python()
    message_json = message.as_json()

.. code-block:: python

    # Version 3.x
    import json

    from aiogram.utils.serialization import deserialize_telegram_object_to_python

    message_dict = deserialize_telegram_object_to_python(message)
    message_json = json.dumps(message_dict)

ChatMember tools
----------------

.. note::

    The tools below (:code:`ChatMemberAdapter`, :code:`ADMINS`, :code:`MEMBERS`)
    were added in aiogram **3.9**; on earlier 3.x releases, use
    :func:`isinstance` checks against the concrete :code:`ChatMember*` classes
    directly.

- Now :class:`aiogram.types.chat_member.ChatMember` no longer contains tools to resolve an object with the appropriate status.

  .. code-block:: python

      # Version 2.x
      from aiogram.types import ChatMember

      chat_member = ChatMember.resolve(**dict_data)

  .. code-block:: python

      # Version 3.x
      from aiogram.utils.chat_member import ChatMemberAdapter

      chat_member = ChatMemberAdapter.validate_python(dict_data)

- Now :class:`aiogram.types.chat_member.ChatMember` and all its child classes no longer
  contain methods for checking for membership in certain logical groups.
  As a substitute, you can use pre-defined groups or create such groups yourself
  and check their entry using the :func:`isinstance` function

  .. code-block:: python

      # Version 2.x
      if chat_member.is_chat_admin():
          print("ChatMember is chat admin")

      if chat_member.is_chat_member():
          print("ChatMember is in the chat")

  .. code-block:: python

      # Version 3.x
      from aiogram.utils.chat_member import ADMINS, MEMBERS

      if isinstance(chat_member, ADMINS):
          print("ChatMember is chat admin")

      if isinstance(chat_member, MEMBERS):
          print("ChatMember is in the chat")

  .. note::
    You also can independently create group similar to ADMINS that fits the logic of your application.

    E.g., you can create a PUNISHED group and include banned and restricted members there!


.. _migration-exceptions:

Exceptions
==========

Mapping (v2 -> v3)
-------------------

All v3 exception classes live in :code:`aiogram.exceptions`.

- :code:`RetryAfter` -> :class:`~aiogram.exceptions.TelegramRetryAfter`
  (key attribute: :code:`retry_after`, int — see the warning below)
- :code:`MigrateToChat` -> :class:`~aiogram.exceptions.TelegramMigrateToChat`
  (key attribute: :code:`migrate_to_chat_id`, int — same name as in v2)
- :code:`BadRequest` (and all of its many v2 subclasses)
  -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`NotFound` -> :class:`~aiogram.exceptions.TelegramNotFound`
- :code:`ConflictError` (including :code:`TerminatedByOtherGetUpdates`)
  -> :class:`~aiogram.exceptions.TelegramConflictError`
- :code:`NetworkError` -> :class:`~aiogram.exceptions.TelegramNetworkError`
- :code:`RestartingTelegram` -> :class:`~aiogram.exceptions.RestartingTelegram`,
  now a subclass of :class:`~aiogram.exceptions.TelegramServerError` (any other HTTP 5xx
  response raises :class:`~aiogram.exceptions.TelegramServerError` itself)
- :code:`Unauthorized` -> **split in two**, see below

The v2 :code:`Unauthorized` family covered two different HTTP statuses, and v3 keeps
them apart:

- an invalid or revoked bot token (HTTP 401)
  -> :class:`~aiogram.exceptions.TelegramUnauthorizedError`
- :code:`Forbidden: ...` responses (HTTP 403) — the bot was blocked by the user, kicked
  from the chat, or the user was deactivated, i.e. v2 :code:`BotBlocked`,
  :code:`BotKicked`, :code:`UserDeactivated`, :code:`CantInitiateConversation`
  -> :class:`~aiogram.exceptions.TelegramForbiddenError`

.. warning::

    Attributes were renamed too, not only the classes. The most important one:
    v2 :code:`RetryAfter.timeout` is now :code:`TelegramRetryAfter.retry_after`.
    An :code:`except` block migrated only by class name compiles fine and crashes
    with :code:`AttributeError` **only under flood limits**:

    .. code-block:: python

        # Version 2.x
        except exceptions.RetryAfter as e:
            await asyncio.sleep(e.timeout)

    .. code-block:: python

        # Version 3.x
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)

    (:code:`migrate_to_chat_id` kept its name from v2 :code:`MigrateToChat`.)

Two v3 classes have no v2 counterpart at all:

- :class:`~aiogram.exceptions.TelegramEntityTooLarge` — HTTP 413, raised for file
  uploads that exceed the server limit
- :class:`~aiogram.exceptions.ClientDecodeError` — raised when the response body cannot
  be decoded; carries :code:`original` (the underlying exception) and :code:`data`
  (the raw response body)

.. warning::

    :code:`except TelegramAPIError` is no longer a catch-all.
    :class:`~aiogram.exceptions.ClientDecodeError` is **not** a subclass of
    :class:`~aiogram.exceptions.TelegramAPIError` — they only share the common base
    :class:`~aiogram.exceptions.AiogramError` — so a v2-style catch-all migrated as
    :code:`except TelegramAPIError` silently stops covering response-parsing errors.
    If you need "catch everything aiogram can raise", catch
    :class:`~aiogram.exceptions.AiogramError`.

    This bites hardest with **self-hosted Bot API servers** — see
    `Telegram API Server`_.

Exceptions removed in v3 (from v2)
----------------------------------

v2 shipped around a hundred fine-grained exception classes that were detected by
matching the error text (:code:`MessageNotModified`, :code:`ChatNotFound`, ...).
None of them exist in v3: exceptions are classified **only by the HTTP status code**
of the response, because Telegram does not document stable error codes.

The v2 class hierarchy tells you which v3 class replaces each name — everything that
derived from v2 :code:`BadRequest` is HTTP 400, while the **subclasses** of v2
:code:`Unauthorized` (:code:`BotBlocked`, :code:`BotKicked`, ...) are delivered by
Telegram as :code:`Forbidden: ...` with HTTP 403 (a bare :code:`Unauthorized` —
an invalid token — is HTTP 401, see the split above):

- :code:`MessageNotModified` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`MessageToEditNotFound` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`MessageToDeleteNotFound` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`MessageCantBeDeleted` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`MessageIsTooLong` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`MessageIdentifierNotSpecified` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`CantParseEntities` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`ChatNotFound` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`InvalidQueryID` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`InvalidStickersSet` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`ChatAdminRequired` -> :class:`~aiogram.exceptions.TelegramBadRequest`
- :code:`BotBlocked` -> :class:`~aiogram.exceptions.TelegramForbiddenError`
- :code:`BotKicked` -> :class:`~aiogram.exceptions.TelegramForbiddenError`
- :code:`UserDeactivated` -> :class:`~aiogram.exceptions.TelegramForbiddenError`
- :code:`CantInitiateConversation` -> :class:`~aiogram.exceptions.TelegramForbiddenError`
- :code:`TerminatedByOtherGetUpdates` -> :class:`~aiogram.exceptions.TelegramConflictError`
- :code:`Throttled` -> removed together with the v2 throttling API
  (see :ref:`Throttling <migration-throttling>`)

.. note::

    Because the classification is by status code only, several unrelated v2 names
    collapse into a single v3 class. If you really need to distinguish a specific cause
    inside :class:`~aiogram.exceptions.TelegramBadRequest`, match on the error text:

    .. code-block:: python

        from aiogram.exceptions import TelegramBadRequest

        try:
            await message.edit_text("Same text")
        except TelegramBadRequest as e:
            if "message is not modified" not in e.message:
                raise

    Keep in mind that these texts are not part of the documented Bot API and may change,
    so use the narrowest check you can and always re-raise what you did not expect.


Error handlers
==============

The signature and registration of error handlers changed completely:

.. code-block:: python

    # Version 2.x
    @dp.errors_handler(exception=MyCustomError)
    async def my_error_handler(update: types.Update, exception: Exception):
        ...
        return True  # mark error as handled, stop propagation

.. code-block:: python

    # Version 3.x
    from aiogram import F
    from aiogram.filters import ExceptionTypeFilter
    from aiogram.types import ErrorEvent, Message

    @router.error(ExceptionTypeFilter(MyCustomError), F.update.message.as_("message"))
    async def my_error_handler(event: ErrorEvent, message: Message) -> None:
        await message.answer("Oops, something went wrong!")

Key differences:

- The handler receives a single :class:`~aiogram.types.error_event.ErrorEvent`
  with :code:`event.update` and :code:`event.exception`, instead of two arguments.
- Filtering by exception type is done with
  :class:`~aiogram.filters.exception.ExceptionTypeFilter` instead of the
  :code:`exception=` keyword.
- v2 semantics "return :code:`True` to stop other error handlers" is gone.
  Error handlers now behave like any other observer: the first handler whose
  filters match handles the error, and propagation stops — no return value is needed.
- Errors unhandled by any error handler are logged by the :code:`aiogram.event` logger.

Read more: :ref:`Error handling docs <error-event>`.


Middlewares
===========

- Middlewares can now control an execution context, e.g., using context managers.
  (:ref:`Read more » <middlewares>`)
- All contextual data is now shared end-to-end between middlewares, filters, and handlers.
  For example now you can easily pass some data into context inside middleware and
  get it in the filters layer as the same way as in the handlers via keyword arguments.
- Added a mechanism named **flags** that helps customize handler behavior
  in conjunction with middlewares. (:ref:`Read more » <flags>`)
- :code:`aiogram.contrib.middlewares.logging.LoggingMiddleware` is removed together with
  the whole :code:`aiogram.contrib` package. Use standard :mod:`logging` configuration
  for aiogram loggers (:code:`aiogram.event` and others), or write a trivial middleware.

.. _migration-throttling:

Throttling
==========

The entire v2 throttling API was removed **with no built-in replacement**:

- :code:`dp.throttle()`, :code:`dp.check_key()`, :code:`dp.release_key()`
- the :code:`Throttled` exception
- the :code:`rate_limit` decorator and the :code:`ThrottlingMiddleware` recipe
  from the official v2 documentation
- :code:`CancelHandler` / :code:`current_handler` used by that recipe
  (in v3 a middleware simply returns without calling :code:`handler(...)`
  to drop an event)
- the "bucket" API of FSM storages (:code:`get_bucket` / :code:`set_bucket`) —
  v3 storages keep only state and data

The v3 approach is an **inner** middleware, optionally configured per-handler with
:ref:`flags <flags>`:

.. code-block:: python

    from collections.abc import Awaitable, Callable
    from time import monotonic
    from typing import Any

    from aiogram import BaseMiddleware
    from aiogram.dispatcher.flags import get_flag
    from aiogram.types import Message


    class ThrottlingMiddleware(BaseMiddleware):
        def __init__(self, default_rate: float = 0.5) -> None:
            self.default_rate = default_rate
            # scoped per (user, handler): one handler's throttle must not
            # suppress unrelated handlers, like v2's per-handler rate_limit
            self.last_call: dict[tuple[int, Any], float] = {}

        async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any],
        ) -> Any:
            if event.from_user is None:  # channel posts have no sender
                return await handler(event, data)

            rate = self.default_rate
            flag = get_flag(data, "rate_limit")
            if flag is not None:
                rate = flag.get("rate", self.default_rate)

            key = (event.from_user.id, data["handler"].callback)
            now = monotonic()
            last = self.last_call.get(key)
            if last is not None and now - last < rate:
                return None  # drop the event
            self.last_call[key] = now
            return await handler(event, data)

.. code-block:: python

    from aiogram import flags

    router.message.middleware(ThrottlingMiddleware())


    @router.message(Command("expensive"))
    @flags.rate_limit(rate=5.0)
    async def handler(message: Message) -> None:
        ...

.. warning::

    Register this as an **inner** middleware, exactly as shown above
    (:code:`router.message.middleware(...)`), not as an outer one
    (:code:`router.message.outer_middleware(...)`). The resolved handler and its
    flags only exist between the outer and the inner middleware layers: in an outer
    middleware :code:`data["handler"]` is not set at all (the example above would
    raise :code:`KeyError`) and :code:`get_flag(data, "rate_limit")` always returns
    :code:`None`.

.. note::

    The recipe is intentionally simple and is **not** a semantic clone of v2
    :code:`dp.throttle()`: v2 did not throttle the first call, keyed buckets by the
    :code:`rate_limit` key rather than by handler, and stored buckets in the FSM
    storage — so limits were shared between replicas of the bot. If you need
    cross-replica throttling, keep the timestamps in your storage (Redis) instead of
    a process-local dict.

.. note::

    The example above keeps timestamps in an unbounded in-memory dict to stay short.
    In production, use a TTL cache or your storage backend, and answer the user
    ("too many requests") instead of dropping silently if that fits your UX.


Keyboard Markup
===============

- Now :class:`aiogram.types.inline_keyboard_markup.InlineKeyboardMarkup`
  and :class:`aiogram.types.reply_keyboard_markup.ReplyKeyboardMarkup` no longer have methods
  for extension, instead you have to use the markup builders
  :class:`aiogram.utils.keyboard.InlineKeyboardBuilder`
  and :class:`aiogram.utils.keyboard.ReplyKeyboardBuilder` respectively
  (:ref:`Read more » <Keyboard builder>`)
- Buttons are constructed with keyword-only arguments now, see
  `Constructors of types and methods are keyword-only`_.


Callbacks data
==============

- The callback data factory is now strictly typed using `pydantic <https://docs.pydantic.dev/>`_ models.
  (:ref:`Read more » <Callback data factory>`)


Finite State machine
====================

- State filters are no longer applied implicitly — see
  `Default state filter behavior is inverted`_.
- Added the possibility to change the FSM strategy. For example,
  if you want to control the state for each user based on chat topics rather than
  the user in a chat, you can specify this in the |Dispatcher|.
- Now :code:`aiogram.fsm.state.State` and :code:`aiogram.fsm.state.StatesGroup` don't have
  helper methods like :code:`.set()`, :code:`.next()`, etc.
  Instead, you should set states by passing them directly to
  :code:`aiogram.fsm.context.FSMContext` (:ref:`Read more » <Finite State Machine>`)
- The state proxy is deprecated; you should update the state data by calling
  :code:`state.set_data(...)` and :code:`state.get_data()` respectively.
- Storages moved from :code:`aiogram.contrib.fsm_storage` to :code:`aiogram.fsm.storage`:

  - :code:`aiogram.contrib.fsm_storage.memory.MemoryStorage` -> :class:`aiogram.fsm.storage.memory.MemoryStorage`
  - :code:`aiogram.contrib.fsm_storage.redis.RedisStorage2` -> :class:`aiogram.fsm.storage.redis.RedisStorage`
  - :code:`aiogram.contrib.fsm_storage.mongo.MongoStorage` -> :class:`aiogram.fsm.storage.mongo.MongoStorage`

Storage keys and migrating live states (Redis)
----------------------------------------------

.. warning::

    If the key format of your v3 storage does not match the keys your v2 bot wrote,
    all live user states are silently "lost" after the deploy: the bot simply reads
    empty state for everyone. Verify key compatibility **before** switching over.

    Note also that a topic-aware FSM strategy inserts an extra :code:`thread_id`
    segment into the key (see below), so check the pattern against **real keys taken
    from your traffic**, not only against the shape shown here.

In v3 the storage key layout is controlled by a
:class:`~aiogram.fsm.storage.base.KeyBuilder`. The default
:class:`~aiogram.fsm.storage.base.DefaultKeyBuilder` produces:

.. code-block:: text

    <prefix>:<bot_id?>:<business_connection_id?>:<chat_id>:<thread_id?>:<user_id>:<destiny?>:<field>

The segments marked with :code:`?` are conditional:

- :code:`bot_id` — only with :code:`with_bot_id=True` (off by default)
- :code:`business_connection_id` — only with :code:`with_business_connection_id=True`
  and when the key actually carries one
- :code:`thread_id` — whenever the key carries one, i.e. with the topic-aware FSM
  strategies; this segment is **not** controlled by a builder option
- :code:`destiny` — only with :code:`with_destiny=True`; without it, a non-default
  destiny raises :code:`ValueError` instead of being silently dropped
- :code:`field` — :code:`state`, :code:`data` or :code:`lock`

With the default builder options and the default FSM strategy this reduces to:

.. code-block:: text

    fsm:<chat_id>:<user_id>:state
    fsm:<chat_id>:<user_id>:data

which matches the **default** v2 :code:`RedisStorage2` layout
(:code:`fsm:<chat>:<user>:state`). But if your v2 setup used a custom
:code:`prefix`, or the older v2 :code:`RedisStorage` (v1-style), the formats differ.
Many v2 layouts can be reproduced by configuring the builder:

.. code-block:: python

    from aiogram.fsm.storage.base import DefaultKeyBuilder
    from aiogram.fsm.storage.redis import RedisStorage

    storage = RedisStorage.from_url(
        "redis://localhost:6379/0",
        key_builder=DefaultKeyBuilder(
            prefix="my_fsm_key",  # your v2 prefix, default "fsm"
            with_bot_id=False,    # v2 keys never contained bot id
        ),
    )

Notes:

- :code:`with_bot_id=True` is recommended for **new** projects and required for
  multibot setups, but it changes the key format — don't enable it while you still
  need to read v2-era keys.
- If you switch the dispatcher to a topic-aware FSM strategy, the keys grow a
  :code:`thread_id` segment and stop matching your v2 keys — that is a separate
  migration, not a drop-in change.
- A :class:`~aiogram.fsm.storage.base.KeyBuilder` only controls key **names**, not the
  record layout. The old (non-2) v2 :code:`RedisStorage` stored one JSON blob
  (:code:`{"state": ..., "data": ..., "bucket": ...}`) per :code:`fsm:<chat>:<user>`
  key — no key builder can make v3 read that; the only path is a one-off script that
  splits each record into the v3 :code:`...:state` / :code:`...:data` keys.
- With v2 :code:`RedisStorage2`, there was a third record type next to
  :code:`...:state` / :code:`...:data` — the :code:`...:bucket` keys of the removed
  throttling API; v3 never reads them, so they can be deleted.
- Check with :code:`redis-cli --scan --pattern 'fsm:*'` (or your prefix) that the v3 bot
  reads and writes exactly the same keys as the v2 bot did.


Sending Files
=============

In v2 you could pass an IO object directly to the API method or wrap it in the
:code:`InputFile` class. In v3, :class:`~aiogram.types.input_file.InputFile` is
**abstract** and cannot be instantiated or receive raw IO objects — use one of the
concrete classes:

- :class:`~aiogram.types.input_file.FSInputFile` — file on the local filesystem
- :class:`~aiogram.types.input_file.BufferedInputFile` — :code:`bytes` in memory
- :class:`~aiogram.types.input_file.URLInputFile` — file by URL

.. code-block:: python

    # Version 2.x
    await bot.send_photo(chat_id, photo=open("photo.png", "rb"))
    # or
    await bot.send_photo(chat_id, photo=types.InputFile("photo.png"))

.. code-block:: python

    # Version 3.x
    from aiogram.types import FSInputFile

    await bot.send_photo(chat_id, photo=FSInputFile("photo.png"))

(:ref:`Read more » <sending-files>`)


Utilities and contrib
=====================

The whole :code:`aiogram.contrib` package is removed. Where its contents went:

- :code:`aiogram.contrib.fsm_storage.*` -> :code:`aiogram.fsm.storage.*`
  (see `Finite State machine`_)
- :code:`aiogram.contrib.middlewares.logging.LoggingMiddleware` -> removed,
  use standard :mod:`logging` (see `Middlewares`_)
- :code:`aiogram.contrib.middlewares.i18n.I18nMiddleware` -> :code:`aiogram.utils.i18n`
  (see :ref:`below <migration-i18n>` and :doc:`Translation </utils/i18n>`)

Other utility changes:

- :code:`aiogram.utils.json` (JSON library selection) is removed without replacement;
  aiogram handles serialization internally.
- :code:`aiogram.utils.mixins` and :code:`ContextInstanceMixin` still exist and custom
  classes built on them migrate unchanged; what *was* removed is the built-in context on
  |Bot|, |Dispatcher| and Telegram types (see `Dispatcher`_).
- :code:`types.ChatActions` helpers are removed. Use the
  :class:`aiogram.enums.chat_action.ChatAction` enum with an explicit call, or the
  :class:`~aiogram.utils.chat_action.ChatActionSender` helper:

  .. code-block:: python

      # Version 2.x
      await types.ChatActions.typing()

  .. code-block:: python

      # Version 3.x
      from aiogram.enums import ChatAction

      await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

  To keep the action alive for the duration of a long operation, use the context
  manager:

  .. code-block:: python

      from aiogram.utils.chat_action import ChatActionSender

      async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
          await long_operation()

  The same thing can be done per handler with
  :class:`~aiogram.utils.chat_action.ChatActionMiddleware` and the
  :code:`@flags.chat_action(...)` decorator, following the same :ref:`flags <flags>`
  mechanism shown in the :ref:`Throttling <migration-throttling>` section.

.. _migration-i18n:

I18n
----

The i18n machinery moved from :code:`aiogram.contrib.middlewares.i18n` to
:code:`aiogram.utils.i18n` and the API changed completely — the v2
:code:`I18nMiddleware` with its :code:`trigger`/:code:`gettext` methods is replaced by
the :code:`aiogram.utils.i18n.I18n` core class plus a set of middlewares.
The canonical reference for the v3 API is :doc:`Translation </utils/i18n>`; this section
only covers what changes when you come from v2.

.. code-block:: python

    # Version 2.x
    from aiogram.contrib.middlewares.i18n import I18nMiddleware

    i18n = I18nMiddleware("mybot", LOCALES_DIR)
    dp.middleware.setup(i18n)
    _ = i18n.gettext

.. code-block:: python

    # Version 3.x
    from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
    from aiogram.utils.i18n import gettext as _

    i18n = I18n(path="locales", default_locale="en", domain="mybot")
    SimpleI18nMiddleware(i18n).setup(dp)

Available middlewares:

- :class:`~aiogram.utils.i18n.middleware.SimpleI18nMiddleware` — locale from the
  user's :code:`language_code`
- :class:`~aiogram.utils.i18n.middleware.ConstI18nMiddleware` — fixed locale
- :class:`~aiogram.utils.i18n.middleware.FSMI18nMiddleware` — locale stored in FSM
- subclass :class:`~aiogram.utils.i18n.middleware.I18nMiddleware` and override
  :code:`get_locale` for custom resolution (e.g. from a database)

Lazy translations are available via :code:`aiogram.utils.i18n.lazy_gettext`.

.. note::

    :code:`I18n` scans and loads locales **in its
    constructor**. A :code:`.po` file without a compiled :code:`.mo` in the configured
    domain raises :code:`RuntimeError` immediately at startup (often at import time) —
    in v2 the same problem surfaced later. Make sure compiling catalogs
    (:code:`pybabel compile -d locales -D mybot`) is part of your build/deploy.


Webhook
=======

- The aiohttp web app configuration has been simplified.
- aiogram can serialize a method returned from a handler — including file uploads —
  directly into the webhook HTTP response
  (`make requests in response to updates <https://core.telegram.org/bots/faq#how-can-i-make-requests-in-response-to-updates>`_);
  see `Replying into the webhook response`_ below for when this is actually enabled.

Replying into the webhook response
----------------------------------

The v2 helpers for answering directly in the webhook HTTP response —
:code:`aiogram.dispatcher.webhook.SendMessage`, :code:`DeleteMessage`, etc. with
:code:`.get_response()` — were removed.

- If you serve the webhook with aiogram's own aiohttp application
  (:class:`~aiogram.webhook.aiohttp_server.SimpleRequestHandler`), return a method
  object from the handler and it is serialized into the webhook response
  (including file uploads) — but **only** with
  :code:`SimpleRequestHandler(..., handle_in_background=False)`. The default is
  :code:`handle_in_background=True`, which answers Telegram with an empty response
  immediately and sends any returned method as a separate Bot API request instead.
- If you plug aiogram into a **third-party web framework** (FastAPI, Sanic, ...),
  the direct equivalent of v2 :code:`.get_response()` is
  :func:`~aiogram.utils.serialization.deserialize_telegram_object_to_python`,
  which produces the same payload from any method object (the API method name is
  included by default via :code:`include_api_method_name=True`):

  .. code-block:: python

      # Version 2.x
      from aiogram.dispatcher.webhook import DeleteMessage

      return DeleteMessage(chat_id=..., message_id=...).get_response()

  .. code-block:: python

      # Version 3.x
      from aiogram.methods import DeleteMessage
      from aiogram.utils.serialization import deserialize_telegram_object_to_python

      return deserialize_telegram_object_to_python(
          DeleteMessage(chat_id=..., message_id=...),
          include_api_method_name=True,
      )

  If your :class:`~aiogram.client.bot.Bot` is configured with
  :code:`DefaultBotProperties`, pass them too —
  :code:`deserialize_telegram_object_to_python(method, default=bot.default, ...)` —
  otherwise defaults such as :code:`parse_mode` are silently omitted from the
  payload. Note that file uploads cannot be answered this way (they require a
  multipart response body); send them with a regular API call instead.


Telegram API Server
===================

- The :obj:`server` parameter has been moved from the |Bot| instance to :obj:`api` parameter of the :class:`~aiogram.client.session.base.BaseSession`.
- The constant :obj:`aiogram.bot.api.TELEGRAM_PRODUCTION` has been moved to :obj:`aiogram.client.telegram.PRODUCTION`.
- If you run a **self-hosted Bot API server**, upgrade it together with aiogram.
  aiogram 3.x declares fields from recent Bot API versions as required (e.g.
  :code:`ChatMemberRestricted.can_react_to_messages`), so responses from a server
  lagging a few versions behind fail pydantic validation — every affected call
  raises :code:`ClientDecodeError`, bypassing :code:`except TelegramAPIError`
  handlers entirely (see the :ref:`Exceptions section <migration-exceptions>`).
