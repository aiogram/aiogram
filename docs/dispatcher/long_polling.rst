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

Example
=======

This example will show you how to create simple echo bot based on long-polling.

.. literalinclude:: ../../examples/echo_bot.py
