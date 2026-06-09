.. _flags:

=====
Flags
=====

Flags is a markers for handlers that can be used in `middlewares <#use-in-middlewares>`_
or special `utilities <#use-in-utilities>`_ to make classification of the handlers.

Flags can be added to the handler via `decorators <#via-decorators>`_,
`handlers registration <#via-handler-registration-method>`_ or
`filters <via-filters>`_.

Via decorators
==============

For example mark handler with `chat_action` flag

.. code-block:: python

    from aiogram import flags

    @flags.chat_action
    async def my_handler(message: Message)

Or just for rate-limit or something else

.. code-block:: python

    from aiogram import flags

    @flags.rate_limit(rate=2, key="something")
    async def my_handler(message: Message)

Via handler registration method
===============================

.. code-block:: python

    @router.message(..., flags={'chat_action': 'typing', 'rate_limit': {'rate': 5}})

Via filters
===========

.. code-block:: python

    class Command(Filter):
        ...

        def update_handler_flags(self, flags: Dict[str, Any]) -> None:
            commands = flags.setdefault("commands", [])
            commands.append(self)



Use in middlewares
==================

.. automodule:: aiogram.dispatcher.flags
    :members: extract_flags, get_flag, check_flags


Example in middlewares
----------------------

.. code-block:: python

    async def my_middleware(handler, event, data):
        typing = get_flag(data, "typing")  # Check that handler marked with `typing` flag
        if not typing:
            return await handler(event, data)

        async with ChatActionSender.typing(chat_id=event.chat.id):
            return await handler(event, data)

Use in utilities
================

For example you can collect all registered commands with handler description and then it can be used for generating commands help

.. code-block:: python

    def collect_commands(router: Router) -> Generator[Tuple[Command, str], None, None]:
        for handler in router.message.handlers:
            if "commands" not in handler.flags:  # ignore all handler without commands
                continue
            # the Command filter adds the flag with list of commands attached to the handler
            for command in handler.flags["commands"]:
                yield command, handler.callback.__doc__ or ""
        # Recursively extract commands from nested routers
        for sub_router in router.sub_routers:
            yield from collect_commands(sub_router)
