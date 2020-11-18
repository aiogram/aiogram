##############
kickChatMember
##############

Use this method to kick a user from a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the group on their own using invite links, etc., unless unbanned first. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.kick_chat_member
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.kick_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import KickChatMember`
- :code:`from aiogram.methods import KickChatMember`
- :code:`from aiogram.methods.kick_chat_member import KickChatMember`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await KickChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(KickChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return KickChatMember(...)