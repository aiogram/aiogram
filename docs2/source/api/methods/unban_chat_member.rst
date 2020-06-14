###############
unbanChatMember
###############

Use this method to unban a previously kicked user in a supergroup or channel. The user will not return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.unban_chat_member
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.unban_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import UnbanChatMember`
- :code:`from aiogram.api.methods import UnbanChatMember`
- :code:`from aiogram.api.methods.unban_chat_member import UnbanChatMember`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await UnbanChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(UnbanChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return UnbanChatMember(...)