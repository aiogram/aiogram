####################
Dependency injection
####################

Dependency injection is a programming technique that makes a class independent of its dependencies.
It achieves that by decoupling the usage of an object from its creation.
This helps you to follow `SOLID's <https://en.wikipedia.org/wiki/SOLID>`_ dependency
inversion and single responsibility principles.


How it works in aiogram
=======================

For each update :class:`aiogram.dispatcher.dispatcher.Dispatcher` passes handling context data.
Filters and middleware can also make changes to the context.

To access contextual data you should specify corresponding keyword parameter in handler or filter.
For example, to get :class:`aiogram.fsm.context.FSMContext` we do it like that:

.. code-block:: python

    @router.message(ProfileCompletion.add_photo, F.photo)
    async def add_photo(
        message: types.Message, bot: Bot, state: FSMContext
    ) -> Any:
        ... # do something with photo


Injecting own dependencies
==========================

Aiogram provides several ways to complement / modify contextual data.

The first and easiest way is to simply specify the named arguments in
:class:`aiogram.dispatcher.dispatcher.Dispatcher` initialization, polling start methods
or :class:`aiogram.webhook.aiohttp_server.SimpleRequestHandler` initialization if you use webhooks.

.. code-block:: python

    async def main() -> None:
        dp = Dispatcher(..., foo=42)
        return await dp.start_polling(
            bot, bar="Bazz"
        )

Analogy for webhook:

.. code-block:: python

    async def main() -> None:
        dp = Dispatcher(..., foo=42)
        handler = SimpleRequestHandler(dispatcher=dp, bot=bot, bar="Bazz")
        ... # starting webhook

:class:`aiogram.dispatcher.dispatcher.Dispatcher`'s workflow data also can be supplemented
through :code:`workflow_data` before start (:code:`dp["eggs"]` reads it back;
item assignment :code:`dp["eggs"] = ...` is removed in 4.0):

.. code-block:: python

    dp = Dispatcher(...)
    dp.workflow_data["eggs"] = Spam()

The middlewares updates the context quite often.
You can read more about them on this page:

- :ref:`Middlewares <middlewares>`

The last way is to return a dictionary from the filter:

.. literalinclude:: ../../examples/context_addition_from_filter.py

...or using :ref:`MagicFilter <magic-filters>` with :code:`.as_(...)` method.


Using type hints
================

.. note::

    Type-hinting middleware data is optional and is not required for the correct operation of the dispatcher.
    However, it is recommended to use it to improve the readability of the code.

Keys become available at different points of an update's path, so
:mod:`aiogram.dispatcher.middlewares.data` has one :class:`~typing.TypedDict` per point:

.. list-table::
    :header-rows: 1

    * - Type
      - Use it in
      - Adds
    * - :class:`~aiogram.dispatcher.middlewares.data.OuterData`
      - :code:`dp.update` outer middlewares; also filters, inner middlewares and handlers registered
        on :code:`dp.update` itself, and :code:`errors` handlers
      - :code:`dispatcher`, :code:`bot`, :code:`event_context`; :code:`bots` (polling only) and
        :code:`fsm_storage` (unless :code:`disable_fsm=True`) are optional
    * - :class:`~aiogram.dispatcher.middlewares.data.RouterOuterData`
      - router-level outer middlewares (:code:`router.message.outer_middleware`)
      - :code:`event_update`, :code:`event_router`; :code:`state` and :code:`raw_state` are optional
    * - :class:`~aiogram.dispatcher.middlewares.data.AiogramData`
      - inner middlewares, filters and handlers of the event observers (:code:`router.message`, ...)
      - :code:`handler`; :code:`i18n` and :code:`i18n_middleware` are optional (set by the i18n middleware with its default keys)

The :code:`dp.update` observer runs before the update is routed, and :code:`errors` handlers receive the
data of the failed update's outer middlewares, so neither gets :code:`event_update` (nor, on :code:`dp.update`,
:code:`event_router`): annotate them with :class:`~aiogram.dispatcher.middlewares.data.OuterData` and read
the other keys with :code:`.get`.

Required keys are always there, so :code:`data["bot"]` type-checks without narrowing; optional keys are read
with :code:`data.get(...)`. A key the type doesn't have is a type error, e.g. :code:`data["handler"]` in an
outer middleware.

The built-in FSM middleware is itself a :code:`dp.update` outer middleware, so outer middlewares registered
after it can see :code:`state` and :code:`raw_state` at runtime; :class:`~aiogram.dispatcher.middlewares.data.OuterData` leaves them out because
that depends on registration order. Read them with :code:`data.get("state")` there.

Extend the type with the keys your own middlewares add and use it through :pep:`692` in a handler:

.. code-block:: python

    from typing import Unpack

    from aiogram.dispatcher.middlewares.data import AiogramData


    class AppData(AiogramData):  # inner data: handlers, filters, inner middlewares
        db: Database             # set by your outer middleware


    @router.message(Command("start"))
    async def start(message: Message, **kw: Unpack[AppData]) -> None:
        await kw["db"].touch(message.chat.id)  # kw["bot"] is a Bot, kw["db"] a Database

.. warning::

    :class:`~aiogram.dispatcher.middlewares.base.BaseMiddleware` still declares :code:`data: dict[str, Any]`, so
    annotating :code:`data` with one of these types in a :code:`__call__` override is reported by mypy as a
    Liskov substitution violation. You can ignore it with a :code:`# type: ignore[override]` comment.

.. note::

    :code:`MiddlewareData` is a deprecated alias of :class:`~aiogram.dispatcher.middlewares.data.AiogramData` (AG4060). The 3.x :code:`FSMData`
    TypedDict is renamed :class:`~aiogram.dispatcher.middlewares.data.FSMKeysData`; :code:`DispatcherData`, :code:`UserContextData` and
    :code:`I18nData` are removed (AG4059).


Available context data types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: aiogram.dispatcher.middlewares.data.OuterData
    :members:
    :undoc-members:
    :member-order: bysource

.. autoclass:: aiogram.dispatcher.middlewares.data.RouterOuterData
    :members:
    :undoc-members:
    :member-order: bysource

.. autoclass:: aiogram.dispatcher.middlewares.data.AiogramData
    :members:
    :undoc-members:
    :member-order: bysource

.. autoclass:: aiogram.dispatcher.middlewares.data.FSMKeysData
    :members:
    :undoc-members:
    :member-order: bysource
