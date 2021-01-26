#############
getChatMember
#############

Returns: :obj:`ChatMember`

.. automodule:: aiogram.methods.get_chat_member
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.get_chat_member import GetChatMember`
- alias: :code:`from aiogram.methods import GetChatMember`

In handlers with current bot
----------------------------

.. code-block:: python

    result: ChatMember = await GetChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatMember = await bot(GetChatMember(...))

