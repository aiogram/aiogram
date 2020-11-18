#############
getChatMember
#############

Use this method to get information about a member of a chat. Returns a ChatMember object on success.

Returns: :obj:`ChatMember`

.. automodule:: aiogram.methods.get_chat_member
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


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
- :code:`from aiogram.methods import GetChatMember`
- :code:`from aiogram.methods.get_chat_member import GetChatMember`

In handlers with current bot
----------------------------

.. code-block::

    result: ChatMember = await GetChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: ChatMember = await bot(GetChatMember(...))

