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

.. toctree::

    router
    dispatcher
    class_based_handlers/index
    filters/index
    middlewares
    finite_state_machine/index
    flags
    errors
