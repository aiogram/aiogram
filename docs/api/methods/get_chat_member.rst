#############
getChatMember
#############

Returns: :obj:`Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned]`

.. automodule:: aiogram.methods.get_chat_member
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned] = await bot.get_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat_member import GetChatMember`
- alias: :code:`from aiogram.methods import GetChatMember`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned] = await GetChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned] = await bot(GetChatMember(...))
