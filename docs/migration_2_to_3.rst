.. |Bot| replace:: :class:`~aiogram.client.bot.Bot`
.. |Dispatcher| replace:: :class:`~aiogram.dispatcher.dispatcher.Dispatcher`
.. |Router| replace:: :class:`~aiogram.dispatcher.router.Router`

==========================
Migration FAQ (2.x -> 3.0)
==========================

.. danger::

    This guide is still in progress.

This version introduces numerous breaking changes and architectural improvements.
It helps reduce the count of global variables in your code, provides useful mechanisms
to modularize your code, and enables the creation of shareable modules via packages on PyPI.
It also makes middlewares and filters more controllable, among other improvements.


On this page, you can read about the changes made in relation to the last stable 2.x version.

.. note::

    This page more closely resembles a detailed changelog than a migration guide,
    but it will be updated in the future.

    Feel free to contribute to this page, if you find something that is not mentioned here.

Dependencies
============

- The dependencies required for :code:`i18n` are no longer part of the default package.
  If your application uses translation functionality, be sure to add an optional dependency:

  :code:`pip install aiogram[i18n]`


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
- The :class:`Executor` has been entirely removed; you can now use the |Dispatcher| directly to start poll the API or handle webhooks from it.
- The throttling method has been completely removed; you can now use middlewares to control
  the execution context and implement any throttling mechanism you desire.
- Removed global context variables from the API types, |Bot| and |Dispatcher| object.
  From now on, if you want to access the current bot instance within handlers or filters,
  you should accept the argument :code:`bot: Bot` and use it instead of :code:`Bot.get_current()`.
  In middlewares, it can be accessed via :code:`data["bot"]`.
- To skip pending updates, you should now call the :class:`~aiogram.methods.delete_webhook.DeleteWebhook` method directly, rather than passing :code:`skip_updates=True` to the start polling method.
- To feed updates to the |Dispatcher|, instead of method :meth:`process_update`,
  you should use method :meth:`~aiogram.dispatcher.dispatcher.Dispatcher.feed_update`.
  (:ref:`Read more » <Handling updates>`)


Filtering events
================

- Keyword filters can no longer be used; use filters explicitly. (`Read more » <https://github.com/aiogram/aiogram/issues/942>`_)
- Due to the removal of keyword filters, all previously enabled-by-default filters
  (such as state and content_type) are now disabled.
  You must specify them explicitly if you wish to use them.
  For example instead of using :code:`@dp.message_handler(content_types=ContentType.PHOTO)`
  you should use :code:`@router.message(F.photo)`
- Most common filters have been replaced with the "magic filter." (:ref:`Read more » <magic-filters>`)
- By default, the message handler now receives any content type.
  If you want a specific one, simply add the appropriate filters (Magic or any other).
- The state filter is no longer enabled by default. This means that if you used :code:`state="*"`
  in v2, you should not pass any state filter in v3.
  Conversely, if the state was not specified in v2, you will now need to specify it in v3.
- Added the possibility to register global filters for each router, which helps to reduce code
  repetition and provides an easier way to control the purpose of each router.



Bot API
=======

- All API methods are now classes with validation, implemented via
  `pydantic <https://docs.pydantic.dev/>`_.
  These API calls are also available as methods in the Bot class.
- More pre-defined Enums have been added and moved to the `aiogram.enums` sub-package.
  For example, the chat type enum is now :class:`aiogram.enums.ChatType` instead of :class:`aiogram.types.chat.ChatType`.
- The HTTP client session has been separated into a container that can be reused
  across different Bot instances within the application.
- API Exceptions are no longer classified by specific messages,
  as Telegram has no documented error codes.
  However, all errors are classified by HTTP status codes, and for each method,
  only one type of error can be associated with a given code.
  Therefore, in most cases, you should check only the error type (by status code)
  without inspecting the error message. More details can be found in the
  :ref:`exceptions section » <exceptions>`.


Exceptions
==========

Mapping (v2 -> v3)
-------------------

- RetryAfter -> :class:`TelegramRetryAfter` (:mod:`aiogram.exceptions`)
  - Important attribute in v3: ``retry_after`` (int).

- ChatMigrated / MigrateToChat -> :class:`TelegramMigrateToChat`
  - Important attribute in v3: ``migrate_to_chat_id`` (int).

- ClientDecodeError -> :class:`ClientDecodeError`
  - Important attributes in v3: ``original`` (Exception) and ``data`` (response body).

- BadRequest -> :class:`TelegramBadRequest`
- Unauthorized -> :class:`TelegramUnauthorizedError`
- Forbidden -> :class:`TelegramForbiddenError`
- NotFound -> :class:`TelegramNotFound`
- Conflict -> :class:`TelegramConflictError`
- ServerError -> :class:`TelegramServerError`
- NetworkError -> :class:`TelegramNetworkError`
- EntityTooLarge -> :class:`TelegramEntityTooLarge`


Exceptions removed in v3 (from v2)
----------------------------------

The list below contains common exception names that appeared in aiogram v2 but
are not defined as separate classes in the v3 codebase. For each v2 name, a
recommended v3 replacement (or handling) is provided — keep your migration
logic simple and rely on the v3 exception classes and their attributes.

- MessageNotModified -> :class:`TelegramBadRequest`
- MessageToEditNotFound -> :class:`TelegramNotFound`
- MessageToDeleteNotFound -> :class:`TelegramNotFound`
- MessageCantBeDeleted -> :class:`TelegramForbiddenError` / :class:`TelegramBadRequest`
- CantParseEntities -> :class:`TelegramBadRequest`
- MessageIsTooLong -> :class:`TelegramEntityTooLarge`
- MessageIdentifierNotFound -> :class:`TelegramNotFound`
- UserDeactivated -> :class:`TelegramForbiddenError`
- CantInitiateConversation -> :class:`TelegramBadRequest`
- StickerSetNameInvalid -> :class:`TelegramBadRequest`
- ChatAdminRequired -> :class:`TelegramForbiddenError`

Use these replacements when migrating exception handling from v2 to v3. If
you relied on catching very specific v2 exception classes, replace those
handlers with the corresponding v3 class above (or catch a broader v3 class
such as :class:`TelegramBadRequest` / :class:`TelegramAPIError`) and inspect
available attributes (see "Mapping (v2 -> v3)") for any required details.


Middlewares
===========

- Middlewares can now control an execution context, e.g., using context managers.
  (:ref:`Read more » <middlewares>`)
- All contextual data is now shared end-to-end between middlewares, filters, and handlers.
  For example now you can easily pass some data into context inside middleware and
  get it in the filters layer as the same way as in the handlers via keyword arguments.
- Added a mechanism named **flags** that helps customize handler behavior
  in conjunction with middlewares. (:ref:`Read more » <flags>`)


Keyboard Markup
===============

- Now :class:`aiogram.types.inline_keyboard_markup.InlineKeyboardMarkup`
  and :class:`aiogram.types.reply_keyboard_markup.ReplyKeyboardMarkup` no longer have methods for extension,
  instead you have to use markup builders :class:`aiogram.utils.keyboard.ReplyKeyboardBuilder`
  and :class:`aiogram.utils.keyboard.KeyboardBuilder` respectively
  (:ref:`Read more » <Keyboard builder>`)


Callbacks data
==============

- The callback data factory is now strictly typed using `pydantic <https://docs.pydantic.dev/>`_ models.
  (:ref:`Read more » <Callback data factory>`)


Finite State machine
====================

- State filters will no longer be automatically added to all handlers;
  you will need to specify the state if you want to use it.
- Added the possibility to change the FSM strategy. For example,
  if you want to control the state for each user based on chat topics rather than
  the user in a chat, you can specify this in the |Dispatcher|.
- Now :class:`aiogram.fsm.state.State` and :class:`aiogram.fsm.state.StateGroup` don't have helper
  methods like :code:`.set()`, :code:`.next()`, etc.
  Instead, you should set states by passing them directly to
  :class:`aiogram.fsm.context.FSMContext` (:ref:`Read more » <Finite State Machine>`)
- The state proxy is deprecated; you should update the state data by calling
  :code:`state.set_data(...)` and :code:`state.get_data()` respectively.


Sending Files
=============

- From now on, you should wrap files in an InputFile object before sending them,
  instead of passing the IO object directly to the API method. (:ref:`Read more » <sending-files>`)


Webhook
=======

- The aiohttp web app configuration has been simplified.
- By default, the ability to upload files has been added when you `make requests in response to updates <https://core.telegram.org/bots/faq#how-can-i-make-requests-in-response-to-updates>`_ (available for webhook only).


Telegram API Server
===================

- The :obj:`server` parameter has been moved from the |Bot| instance to :obj:`api` parameter of the :class:`~aiogram.client.session.base.BaseSession`.
- The constant :obj:`aiogram.bot.api.TELEGRAM_PRODUCTION` has been moved to :obj:`aiogram.client.telegram.PRODUCTION`.


Telegram objects transformation (to dict, to json, from json)
=============================================================

- Methods :code:`TelegramObject.to_object()`, :code:`TelegramObject.to_json()` and :code:`TelegramObject.to_python()`
  have been removed due to the use of `pydantic <https://docs.pydantic.dev/>`_ models.
- :code:`TelegramObject.to_object()` should be replaced by :code:`TelegramObject.model_validate()`
  (`Read more <https://docs.pydantic.dev/2.7/api/base_model/#pydantic.BaseModel.model_validate>`_)
- :code:`TelegramObject.as_json()` should be replaced by :func:`aiogram.utils.serialization.deserialize_telegram_object_to_python`
- :code:`<TelegramObject>.to_python()` should be replaced by :code:`json.dumps(deserialize_telegram_object_to_python(<TelegramObject>))`

Here are some usage examples:

- Creating an object from a dictionary representation of an object

  .. code-block::

    # Version 2.x
    message_dict = {"id": 42, ...}
    message_obj = Message.to_object(message_dict)
    print(message_obj)
    # id=42 name='n' ...
    print(type(message_obj))
    # <class 'aiogram.types.message.Message'>

  .. code-block::

    # Version 3.x
    message_dict = {"id": 42, ...}
    message_obj = Message.model_validate(message_dict)
    print(message_obj)
    # id=42 name='n' ...
    print(type(message_obj))
    # <class 'aiogram.types.message.Message'>

- Creating a json representation of an object

  .. code-block::

    # Version 2.x
    async def handler(message: Message) -> None:
        message_json = message.as_json()
        print(message_json)
        # {"id": 42, ...}
        print(type(message_json))
        # <class 'str'>

  .. code-block::

    # Version 3.x
    async def handler(message: Message) -> None:
        message_json = json.dumps(deserialize_telegram_object_to_python(message))
        print(message_json)
        # {"id": 42, ...}
        print(type(message_json))
        # <class 'str'>

- Creating a dictionary representation of an object

  .. code-block::

    async def handler(message: Message) -> None:
        # Version 2.x
        message_dict = message.to_python()
        print(message_dict)
        # {"id": 42, ...}
        print(type(message_dict))
        # <class 'dict'>

  .. code-block::

    async def handler(message: Message) -> None:
        # Version 3.x
        message_dict = deserialize_telegram_object_to_python(message)
        print(message_dict)
        # {"id": 42, ...}
        print(type(message_dict))
        # <class 'dict'>


ChatMember tools
================

- Now :class:`aiogram.types.chat_member.ChatMember` no longer contains tools to resolve an object with the appropriate status.

  .. code-block::

    # Version 2.x
    from aiogram.types import ChatMember

    chat_member = ChatMember.resolve(**dict_data)

  .. code-block::

    # Version 3.x
    from aiogram.utils.chat_member import ChatMemberAdapter

    chat_member = ChatMemberAdapter.validate_python(dict_data)


- Now :class:`aiogram.types.chat_member.ChatMember` and all its child classes no longer
  contain methods for checking for membership in certain logical groups.
  As a substitute, you can use pre-defined groups or create such groups yourself
  and check their entry using the :func:`isinstance` function

  .. code-block::

    # Version 2.x

    if chat_member.is_chat_admin():
        print("ChatMember is chat admin")

    if chat_member.is_chat_member():
        print("ChatMember is in the chat")

  .. code-block::

    # Version 3.x

    from aiogram.utils.chat_member import ADMINS, MEMBERS

    if isinstance(chat_member, ADMINS):
        print("ChatMember is chat admin")

    if isinstance(chat_member, MEMBERS):
        print("ChatMember is in the chat")

  .. note::
    You also can independently create group similar to ADMINS that fits the logic of your application.

    E.g., you can create a PUNISHED group and include banned and restricted members there!
