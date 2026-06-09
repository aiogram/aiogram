#############
getChatMember
#############

Returns: :obj:`ResultChatMemberUnion`

.. automodule:: aiogram.methods.get_chat_member
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ResultChatMemberUnion = await bot.get_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat_member import GetChatMember`
- alias: :code:`from aiogram.methods import GetChatMember`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ResultChatMemberUnion = await bot(GetChatMember(...))




As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.get_member`
