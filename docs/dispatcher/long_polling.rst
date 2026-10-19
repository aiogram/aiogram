.. _long-polling:

############
Long-polling
############

Long-polling is a technology that allows a Telegram server to send updates in case
when you don't have dedicated IP address or port to receive webhooks for example
on a developer machine.

To use long-polling mode you should use :meth:`aiogram.dispatcher.dispatcher.Dispatcher.start_polling`
or :meth:`aiogram.dispatcher.dispatcher.Dispatcher.run_polling` methods.

.. note::

    You can use polling from only one polling process per single Bot token,
    in other case Telegram server will return an error.

.. note::

    If you will need to scale your bot, you should use webhooks instead of long-polling.

.. note::

    If you will use multibot mode, you should use webhook mode for all bots.

Shutdown
========

With :code:`handle_as_tasks=True` (the default) each update is handled in its own task,
and the update is confirmed to Telegram by the next :code:`getUpdates` request,
which is usually sent before its handler has finished.

By default, stopping polling (by SIGINT/SIGTERM or
:meth:`aiogram.dispatcher.dispatcher.Dispatcher.stop_polling`) does not wait for these handlers:
shutdown callbacks run and bot sessions are closed while they may still be running,
and :meth:`aiogram.dispatcher.dispatcher.Dispatcher.run_polling` cancels the remaining ones
when it closes the event loop. Telegram does not send those updates again.

.. versionadded:: 3.32.0

    The :code:`tasks_shutdown_timeout` parameter of
    :meth:`aiogram.dispatcher.dispatcher.Dispatcher.start_polling` and
    :meth:`aiogram.dispatcher.dispatcher.Dispatcher.run_polling`.

To let the handlers finish, pass the number of seconds to wait for them:

.. code-block:: python

    dp.run_polling(bot, tasks_shutdown_timeout=30)

When polling is stopped, the dispatcher then:

1. stops fetching new updates;
2. waits up to 30 seconds for the updates that are still being handled, of all bots;
3. cancels the handlers still running after that and waits until they have handled
   the cancellation, logging a warning with their number;
4. runs shutdown callbacks and closes bot sessions.

A handler that calls :code:`await dispatcher.stop_polling()` is not waited for:
:code:`stop_polling()` returns once shutdown has completed, and the rest of that handler runs after it.

Keep the timeout shorter than the time your process manager gives the process
between SIGTERM and SIGKILL, so that shutdown callbacks still have time to run.

.. note::

    With :code:`handle_as_tasks=False` the handler runs inside the polling loop and
    :code:`tasks_shutdown_timeout` has no effect: stopping polling cancels the handler at once,
    its update is not confirmed yet, and Telegram sends it again after the next start.

.. note::

    The timeout does not make handling exactly-once. A handler cancelled after the timeout
    leaves its work unfinished, and its update may already be confirmed.
    With :code:`tasks_concurrency_limit`, an update can be handled in full during the wait
    without having been confirmed, and then Telegram sends it again after the next start.
    Handlers with side effects, such as handing over goods after a payment,
    still need to record their progress and to recognise an update they have already handled.

Example
=======

This example will show you how to create simple echo bot based on long-polling.

.. literalinclude:: ../../examples/echo_bot.py
