#############
banChatMember
#############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.ban_chat_member
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.ban_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.ban_chat_member import BanChatMember`
- alias: :code:`from aiogram.methods import BanChatMember`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(BanChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return BanChatMember(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.ban`
