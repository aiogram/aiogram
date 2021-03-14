##############
kickChatMember
##############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.kick_chat_member
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.kick_chat_member import KickChatMember`
- alias: :code:`from aiogram.methods import KickChatMember`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await KickChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(KickChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return KickChatMember(...)
