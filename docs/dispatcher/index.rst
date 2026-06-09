===============
Handling events
===============

*aiogram* includes Dispatcher mechanism.
Dispatcher is needed for handling incoming updates from Telegram.

With dispatcher you can do:

- Handle incoming updates;
- Filter incoming events before it will be processed by specific handler;
- Modify event and related data in middlewares;
- Separate bot functionality between different handlers, modules and packages

Dispatcher is also separated into two entities - Router and Dispatcher.
Dispatcher is subclass of router and should be always is root router.

Telegram supports two ways of receiving updates:

- :ref:`Webhook <webhook>` - you should configure your web server to receive updates from Telegram;
- :ref:`Long polling <long-polling>` - you should request updates from Telegram.

So, you can use both of them with *aiogram*.

.. toctree::

    router
    dispatcher
    dependency_injection
    filters/index
    long_polling
    finite_state_machine/index
    middlewares
    errors
    flags
    webhook
    class_based_handlers/index
