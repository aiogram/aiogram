=======
Command
=======

.. autoclass:: aiogram.filters.command.Command
    :members:
    :member-order: bysource
    :undoc-members: False

When filter is passed the :class:`aiogram.filters.command.CommandObject` will be passed to the handler argument :code:`command`

.. autoclass:: aiogram.filters.command.CommandObject
    :members:
    :member-order: bysource
    :undoc-members: False


Usage
=====

1. Filter single variant of commands: :code:`Command(commands=["start"])` or :code:`Command(commands="start")`
2. Handle command by regexp pattern: :code:`Command(commands=[re.compile(r"item_(\d+)")])`
3. Match command by multiple variants: :code:`Command(commands=["item", re.compile(r"item_(\d+)")])`
4. Handle commands in public chats intended for other bots: :code:`Command(commands=["command"], commands_ignore_mention=True)`

.. warning::

    Command cannot include spaces or any whitespace

Allowed handlers
================

Allowed update types for this filter:

- `message`
- `edited_message`
