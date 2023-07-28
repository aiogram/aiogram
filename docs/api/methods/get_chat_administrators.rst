#####################
getChatAdministrators
#####################

Returns: :obj:`List[Union[ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, ChatMemberLeft, ChatMemberBanned]]`

.. automodule:: aiogram.methods.get_chat_administrators
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


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




As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.get_administrators`
