#############
getMyCommands
#############

Use this method to get the current list of the bot's commands. Requires no parameters. Returns Array of BotCommand on success.

Returns: :obj:`List[BotCommand]`

.. automodule:: aiogram.api.methods.get_my_commands
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: List[BotCommand] = await bot.get_my_commands(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetMyCommands`
- :code:`from aiogram.api.methods import GetMyCommands`
- :code:`from aiogram.api.methods.get_my_commands import GetMyCommands`

In handlers with current bot
----------------------------

.. code-block::

    result: List[BotCommand] = await GetMyCommands(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: List[BotCommand] = await bot(GetMyCommands(...))

