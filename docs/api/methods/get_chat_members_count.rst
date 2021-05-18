###################
getChatMembersCount
###################

Returns: :obj:`int`

.. automodule:: aiogram.methods.get_chat_members_count
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.get_chat_members_count import GetChatMembersCount`
- alias: :code:`from aiogram.methods import GetChatMembersCount`

In handlers with current bot
----------------------------

.. code-block:: python

    result: int = await GetChatMembersCount(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: int = await bot(GetChatMembersCount(...))
