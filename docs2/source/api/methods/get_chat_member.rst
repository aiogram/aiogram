#############
getChatMember
#############

Use this method to get information about a member of a chat. Returns a ChatMember object on success.

Returns: :obj:`ChatMember`

.. automodule:: aiogram.api.methods.get_chat_member
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatMember = await bot.get_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetChatMember`
- :code:`from aiogram.api.methods import GetChatMember`
- :code:`from aiogram.api.methods.get_chat_member import GetChatMember`

In handlers with current bot
----------------------------

.. code-block::

    result: ChatMember = await GetChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: ChatMember = await bot(GetChatMember(...))

