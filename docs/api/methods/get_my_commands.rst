#############
getMyCommands
#############

Returns: :obj:`List[BotCommand]`

.. automodule:: aiogram.methods.get_my_commands
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.get_my_commands import GetMyCommands`
- alias: :code:`from aiogram.methods import GetMyCommands`

In handlers with current bot
----------------------------

.. code-block:: python

    result: List[BotCommand] = await GetMyCommands(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: List[BotCommand] = await bot(GetMyCommands(...))
