###################
unbanChatSenderChat
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.unban_chat_sender_chat
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.unban_chat_sender_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.unban_chat_sender_chat import UnbanChatSenderChat`
- alias: :code:`from aiogram.methods import UnbanChatSenderChat`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(UnbanChatSenderChat(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return UnbanChatSenderChat(...)
