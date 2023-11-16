#############
setMyCommands
#############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_commands
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_my_commands(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_my_commands import SetMyCommands`
- alias: :code:`from aiogram.methods import SetMyCommands`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetMyCommands(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetMyCommands(...)
