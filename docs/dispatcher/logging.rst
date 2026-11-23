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
    for now: they are filled at the dispatch stage boundaries by a later change.
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
(migration id :code:`AG4053`). Configure the :code:`aiogram` parent logger to keep receiving them either way.
:class:`~aiogram.utils.callback_answer.CallbackAnswerMiddleware` keeps logging to :code:`aiogram.middlewares`;
the move covers request records only.

The 3.x loggers :code:`aiogram.client.bot` and :code:`aiogram.utils.chat_action` are gone: their records
are on :code:`aiogram.client` (migration id :code:`AG4054`).


Token redaction
===============

The bot token is part of every Bot API URL (:code:`/bot<token>/getMe`).
Every framework logger masks anything shaped like a bot token as :code:`<bot id>:***`
(:code:`123456:AA...` becomes :code:`123456:***`), so the bot id stays readable. This is on by default.

The filter, :class:`aiogram.loggers.TokenRedactingFilter`, scans:

- the formatted message, arguments included (a :class:`yarl.URL` or an exception as an argument);
- the exception traceback, chained causes included, and :code:`stack_info`;
- string attributes added with :code:`extra=`, and the string values of a :code:`dict` passed that way,
  so a JSON formatter emits them masked. Other values (a :class:`yarl.URL`, a list, a deeper
  :code:`dict`) are not scanned: pass them as strings.

When the traceback holds a token, the record keeps the masked text in :code:`exc_text` and drops
:code:`exc_info`. Standard formatters print the masked traceback. A handler that reads the exception
object itself (an error tracker's logging integration) gets the record without it.

A record without a token is left as it was, so error trackers that group records by message template
keep grouping them. On a match, the message is replaced by its formatted, masked text.

The filter covers the records of :code:`aiogram.*` loggers only. Records of the root logger and of other
libraries (an :code:`aiohttp` access log, for example) reach your handlers unmasked. Attach the same filter
to a handler to cover everything that handler writes:

.. code-block:: python

    import logging

    from aiogram.loggers import TokenRedactingFilter

    handler = logging.StreamHandler()
    handler.addFilter(TokenRedactingFilter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

Any text shaped like a token is masked, including your own content that only looks like one
(digits, a colon, then 30 or more letters, digits, :code:`_` or :code:`-`).

To turn redaction off, for every framework logger and every :class:`~aiogram.loggers.TokenRedactingFilter`
at once, and back on:

.. code-block:: python

    from aiogram import loggers

    loggers.redact_tokens(False)
    loggers.redact_tokens(True)

Error trackers that capture local variables of a stack frame are not covered.

.. autoclass:: aiogram.loggers.TokenRedactingFilter
    :members: filter

.. autofunction:: aiogram.loggers.redact_tokens
