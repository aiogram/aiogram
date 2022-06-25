#####################
getChatAdministrators
#####################

Returns: :obj:`List[Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned]]`

.. automodule:: aiogram.methods.get_chat_administrators
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: List[Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned]] = await bot.get_chat_administrators(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat_administrators import GetChatAdministrators`
- alias: :code:`from aiogram.methods import GetChatAdministrators`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: List[Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned]] = await bot(GetChatAdministrators(...))
