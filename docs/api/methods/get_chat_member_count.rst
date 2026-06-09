##################
getChatMemberCount
##################

Returns: :obj:`int`

.. automodule:: aiogram.methods.get_chat_member_count
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


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




As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.get_member_count`
