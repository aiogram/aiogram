#################
banChatSenderChat
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.ban_chat_sender_chat
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.ban_chat_sender_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.ban_chat_sender_chat import BanChatSenderChat`
- alias: :code:`from aiogram.methods import BanChatSenderChat`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(BanChatSenderChat(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return BanChatSenderChat(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.ban_sender_chat`
