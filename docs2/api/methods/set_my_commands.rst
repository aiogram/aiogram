#############
setMyCommands
#############

Use this method to change the list of the bot's commands. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_commands
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_my_commands(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetMyCommands`
- :code:`from aiogram.methods import SetMyCommands`
- :code:`from aiogram.methods.set_my_commands import SetMyCommands`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetMyCommands(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetMyCommands(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetMyCommands(...)