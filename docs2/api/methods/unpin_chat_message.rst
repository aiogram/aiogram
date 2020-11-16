################
unpinChatMessage
################

Use this method to unpin a message in a group, a supergroup, or a channel. The bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in the supergroup or 'can_edit_messages' admin right in the channel. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.unpin_chat_message
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.unpin_chat_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import UnpinChatMessage`
- :code:`from aiogram.api.methods import UnpinChatMessage`
- :code:`from aiogram.api.methods.unpin_chat_message import UnpinChatMessage`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await UnpinChatMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(UnpinChatMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return UnpinChatMessage(...)