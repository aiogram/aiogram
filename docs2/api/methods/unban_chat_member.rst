###############
unbanChatMember
###############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.unban_chat_member
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.unban_chat_member(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.unban_chat_member import UnbanChatMember`
- alias: :code:`from aiogram.methods import UnbanChatMember`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await UnbanChatMember(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(UnbanChatMember(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return UnbanChatMember(...)