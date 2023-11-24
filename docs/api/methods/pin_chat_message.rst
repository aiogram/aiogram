##############
pinChatMessage
##############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.pin_chat_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.pin_chat_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.pin_chat_message import PinChatMessage`
- alias: :code:`from aiogram.methods import PinChatMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(PinChatMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return PinChatMessage(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.pin_message`
- :meth:`aiogram.types.message.Message.pin`
