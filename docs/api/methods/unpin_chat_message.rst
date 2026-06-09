################
unpinChatMessage
################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.unpin_chat_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.unpin_chat_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.unpin_chat_message import UnpinChatMessage`
- alias: :code:`from aiogram.methods import UnpinChatMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(UnpinChatMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return UnpinChatMessage(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.unpin_message`
- :meth:`aiogram.types.message.Message.unpin`
