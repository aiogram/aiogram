#################
promoteChatMember
#################

Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Pass False for all boolean parameters to demote a user. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.promote_chat_member
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.promote_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import PromoteChatMember`
- :code:`from aiogram.api.methods import PromoteChatMember`
- :code:`from aiogram.api.methods.promote_chat_member import PromoteChatMember`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await PromoteChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(PromoteChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return PromoteChatMember(...)