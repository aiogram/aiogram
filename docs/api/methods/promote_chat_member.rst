#################
promoteChatMember
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.promote_chat_member
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.promote_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.promote_chat_member import PromoteChatMember`
- alias: :code:`from aiogram.methods import PromoteChatMember`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(PromoteChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return PromoteChatMember(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.promote`
