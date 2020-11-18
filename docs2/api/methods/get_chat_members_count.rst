###################
getChatMembersCount
###################

Use this method to get the number of members in a chat. Returns Int on success.

Returns: :obj:`int`

.. automodule:: aiogram.methods.get_chat_members_count
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: int = await bot.get_chat_members_count(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetChatMembersCount`
- :code:`from aiogram.methods import GetChatMembersCount`
- :code:`from aiogram.methods.get_chat_members_count import GetChatMembersCount`

In handlers with current bot
----------------------------

.. code-block::

    result: int = await GetChatMembersCount(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: int = await bot(GetChatMembersCount(...))

