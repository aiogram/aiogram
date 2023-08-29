==========================
Migration FAQ (2.x -> 3.0)
==========================

.. danger::

    This guide is still in progress.

This version introduces much many breaking changes and architectural improvements,
helping to reduce global variables count in your code, provides useful mechanisms
to separate your code to modules or just make sharable modules via packages on the PyPi,
makes middlewares and filters more controllable and others.

On this page you can read about points that changed corresponding to last stable 2.x version.

.. note::

    This page is most like a detailed changelog than a migration guide,
    but it will be updated in the future.

    Feel free to contribute to this page, if you find something that is not mentioned here.


Dispatcher
==========

- :class:`Dispatcher` class no longer accepts the `Bot` instance into the initializer,
  it should be passed to dispatcher only for starting polling or handling event from webhook.
  Also this way adds possibility to use multiple bot instances at the same time ("multibot")
- :class:`Dispatcher` now can be extended with another Dispatcher-like
  thing named :class:`Router` (:ref:`Read more » <Nested routers>`).
  With routes you can easily separate your code to multiple modules
  and may be share this modules between projects.
- Removed the **_handler** suffix from all event handler decorators and registering methods.
  (:ref:`Read more » <Event observers>`)
- Executor entirely removed, now you can use Dispatcher directly to start polling or webhook.
- Throttling method is completely removed, now you can use middlewares to control
  the execution context and use any throttling mechanism you want.
- Removed global context variables from the API types, Bot and Dispatcher object,
  from now if you want to get current bot instance inside handlers or filters you should
  accept the argument :code:`bot: Bot` and use it instead of :code:`Bot.get_current()`
  Inside middlewares it can be accessed via :code:`data["bot"]`.
- Now to skip pending updates, you should call the :class:`aiogram.methods.delete_webhook.DeleteWebhook` method directly instead of passing :code:`skip_updates=True` to start polling method.


Filtering events
================

- Keyword filters can no more be used, use filters explicitly. (`Read more » <https://github.com/aiogram/aiogram/issues/942>`_)
- In due to keyword filters was removed all enabled by default filters (state and content_type now is not enabled),
  so you should specify them explicitly if you want to use.
  For example instead of using :code:`@dp.message_handler(content_types=ContentType.PHOTO)`
  you should use :code:`@router.message(F.photo)`
- Most of common filters is replaced by "magic filter". (:ref:`Read more » <magic-filters>`)
- Now by default message handler receives any content type,
  if you want specific one just add the filters (Magic or any other)
- State filter now is not enabled by default, that's mean if you using :code:`state="*"` in v2
  then you should not pass any state filter in v3, and vice versa,
  if the state in v2 is not specified now you should specify the state.
- Added possibility to register per-router global filters, that helps to reduces
  the number of repetitions in the code and makes easily way to control
  for what each router will be used.


Bot API
=======

- Now all API methods is classes with validation (via `pydantic <https://docs.pydantic.dev/>`_)
  (all API calls is also available as methods in the Bot class).
- Added more pre-defined Enums and moved into `aiogram.enums` sub-package. For example chat type enum now is
  :class:`aiogram.enums.ChatType` instead of :class:`aiogram.types.chat.ChatType`.
  (:ref:`Read more » <enums>`)
- Separated HTTP client session into container that can be reused between different
  Bot instances in the application.
- API Exceptions is no more classified by specific message in due to Telegram has no documented error codes.
  But all errors is classified by HTTP status code and for each method only one case can be caused with the same code,
  so in most cases you should check that only error type (by status-code) without checking error message.
  (:ref:`Read more » <error-types>`)


Middlewares
===========

- Middlewares can now control a execution context, e.g. using context managers (:ref:`Read more » <middlewares>`)
- All contextual data now is shared between middlewares, filters and handlers to end-to-end use.
  For example now you can easily pass some data into context inside middleware and
  get it in the filters layer as the same way as in the handlers via keyword arguments.
- Added mechanism named **flags**, that helps to customize handler behavior
  in conjunction with middlewares. (:ref:`Read more » <flags>`)


Keyboard Markup
===============

- Now :class:`aiogram.types.inline_keyboard_markup.InlineKeyboardMarkup`
  and :class:`aiogram.types.reply_keyboard_markup.ReplyKeyboardMarkup` has no methods to extend it,
  instead you have to use markup builders :class:`aiogram.utils.keyboard.ReplyKeyboardBuilder`
  and :class:`aiogram.utils.keyboard.KeyboardBuilder` respectively
  (:ref:`Read more » <Keyboard builder>`)


Callbacks data
==============

- Callback data factory now is strictly typed via `pydantic <https://docs.pydantic.dev/>`_ models
  (:ref:`Read more » <Callback data factory>`)


Finite State machine
====================

- State filter will no more added to all handlers, you will need to specify state if you want
- Added possibility to change FSM strategy, for example if you want to control state
  for each user in chat topics instead of user in chat you can specify it in the Dispatcher.
- Now :class:`aiogram.fsm.state.State` and :class:`aiogram.fsm.state.StateGroup` don't have helper
  methods like :code:`.set()`, :code:`.next()`, etc.

  Instead of this you should set states by passing them directly to
  :class:`aiogram.fsm.context.FSMContext` (:ref:`Read more » <Finite State Machine>`)
- State proxy is deprecated, you should update the state data by calling
  :code:`state.set_data(...)` and :code:`state.get_data()` respectively.


Sending Files
=============

- From now you should wrap sending files into InputFile object before send instead of passing
  IO object directly to the API method. (:ref:`Read more » <sending-files>`)


Webhook
=======

- Simplified aiohttp web app configuration
- By default added possibility to upload files when you use reply into webhook
