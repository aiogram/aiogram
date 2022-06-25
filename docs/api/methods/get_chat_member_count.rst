##################
getChatMemberCount
##################

Returns: :obj:`int`

.. automodule:: aiogram.methods.get_chat_member_count
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: int = await bot.get_chat_member_count(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat_member_count import GetChatMemberCount`
- alias: :code:`from aiogram.methods import GetChatMemberCount`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: int = await bot(GetChatMemberCount(...))
