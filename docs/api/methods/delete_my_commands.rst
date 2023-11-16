################
deleteMyCommands
################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_my_commands
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_my_commands(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_my_commands import DeleteMyCommands`
- alias: :code:`from aiogram.methods import DeleteMyCommands`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteMyCommands(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteMyCommands(...)
