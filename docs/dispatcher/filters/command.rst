=======
Command
=======

Usage
=====

1. Filter single variant of commands: :code:`Command("start")`
2. Handle command by regexp pattern: :code:`Command(re.compile(r"item_(\\d+)"))`
3. Match command by multiple variants: :code:`Command("item", re.compile(r"item_(\\d+)"))`
4. Handle commands in public chats intended for other bots: :code:`Command("command", ignore_mention=True)`
5. Use :class:`aiogram.types.bot_command.BotCommand` object as command reference :code:`Command(BotCommand(command="command", description="My awesome command")`

.. warning::

    Command cannot include spaces or any whitespace


.. autoclass:: aiogram.filters.command.Command
    :members: __init__
    :member-order: bysource
    :undoc-members: False

When filter is passed the :class:`aiogram.filters.command.CommandObject` will be passed to the handler argument :code:`command`

.. autoclass:: aiogram.filters.command.CommandObject
    :members:
    :member-order: bysource
    :undoc-members: False

Allowed handlers
================

Allowed update types for this filter:

- `message`
- `edited_message`
