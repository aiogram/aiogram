#####################
getChatAdministrators
#####################

Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned.

Returns: :obj:`List[ChatMember]`

.. automodule:: aiogram.api.methods.get_chat_administrators
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: List[ChatMember] = await bot.get_chat_administrators(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetChatAdministrators`
- :code:`from aiogram.api.methods import GetChatAdministrators`
- :code:`from aiogram.api.methods.get_chat_administrators import GetChatAdministrators`

In handlers with current bot
----------------------------

.. code-block::

    result: List[ChatMember] = await GetChatAdministrators(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: List[ChatMember] = await bot(GetChatAdministrators(...))

