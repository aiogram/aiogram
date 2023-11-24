#############
deleteMessage
#############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_message import DeleteMessage`
- alias: :code:`from aiogram.methods import DeleteMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteMessage(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.delete_message`
- :meth:`aiogram.types.message.Message.delete`
