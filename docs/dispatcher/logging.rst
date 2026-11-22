.. _logging:

=======
Logging
=======

*aiogram* logs through the standard :mod:`logging` module.
All framework loggers live under the :code:`aiogram` parent logger,
so :code:`logging.getLogger("aiogram").setLevel(...)` configures all of them at once.


Logger names and record context
===============================

.. list-table::
    :header-rows: 1

    * - Logger
      - Records
    * - :code:`aiogram.dispatcher`
      - dispatcher lifecycle, polling start and stop, tracer failures
    * - :code:`aiogram.event`
      - one record per processed update, unhandled update errors (:code:`exception` level)
    * - :code:`aiogram.runner`
      - reserved for the runner (no records yet)
    * - :code:`aiogram.polling`
      - reserved for the poller (no records yet; polling start and stop are on :code:`aiogram.dispatcher`)
    * - :code:`aiogram.webhook`
      - webhook requests
    * - :code:`aiogram.client`
      - the bot client: session, requests, retries, rate limits, chat actions
    * - :code:`aiogram.fsm`
      - reserved for FSM storages and event isolation (no records yet)
    * - :code:`aiogram.scene`
      - scenes
    * - :code:`aiogram.i18n`
      - reserved for translations (no records yet)
    * - :code:`aiogram.middlewares`
      - :class:`~aiogram.client.session.middlewares.request_logging.RequestLogging`
        and :class:`~aiogram.utils.callback_answer.CallbackAnswerMiddleware` (see below)

Every record from a framework logger has six attributes:

.. list-table::
    :header-rows: 1

    * - Attribute
      - Value
    * - :code:`aiogram_bot_id`
      - id of the bot that received the update
    * - :code:`aiogram_update_id`
      - :code:`update_id` of the update
    * - :code:`aiogram_update_type`
      - event type of the update (:code:`"message"`, :code:`"callback_query"`, ...)
    * - :code:`aiogram_router`
      - name of the router being processed
    * - :code:`aiogram_handler`
      - name of the handler being processed
    * - :code:`aiogram_phase`
      - processing phase

The values are set for the duration of :meth:`Dispatcher.feed_update <aiogram.dispatcher.dispatcher.Dispatcher.feed_update>`,
which every update goes through (polling, webhook and direct calls).
Outside an update, and for values not known yet, the attributes exist and are :code:`None`,
so a format string such as :code:`%(aiogram_update_id)s` never raises.
An attribute passed explicitly with :code:`extra=` is kept.

.. note::

    :code:`aiogram_router`, :code:`aiogram_handler` and :code:`aiogram_phase` are :code:`None`
    for now: they are filled by the dispatch executor once it lands.
    The context object is shared by tasks started during the update, so such a task's records
    show the update's current router, handler and phase.


Context on your own records
---------------------------

:func:`aiogram.loggers.context_filter` returns a :class:`logging.Filter` that copies the same
attributes onto any record. Attach it to a handler to cover your own loggers too,
sync handlers included (they run in a worker thread with the update's context):

.. code-block:: python

    import logging

    from aiogram import loggers

    handler = logging.StreamHandler()
    handler.addFilter(loggers.context_filter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s "
            "update=%(aiogram_update_id)s type=%(aiogram_update_type)s %(message)s"
        )
    )
    logging.basicConfig(level=logging.INFO, handlers=[handler])

A JSON formatter can emit the six attributes as fields.


The :code:`aiogram.middlewares` logger
--------------------------------------

Records of :class:`~aiogram.client.session.middlewares.request_logging.RequestLogging` stay on
:code:`aiogram.middlewares` for one deprecation window, then move to :code:`aiogram.client`
(migration id :code:`AG4052`). Configure the :code:`aiogram` parent logger to keep receiving them either way.
:class:`~aiogram.utils.callback_answer.CallbackAnswerMiddleware` keeps logging to :code:`aiogram.middlewares`;
the move covers request records only.

The 3.x loggers :code:`aiogram.client.bot` and :code:`aiogram.utils.chat_action` are gone: their records
are on :code:`aiogram.client` (migration id :code:`AG4053`).
