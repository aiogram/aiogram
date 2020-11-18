##############
pinChatMessage
##############

Use this method to pin a message in a group, a supergroup, or a channel. The bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in the supergroup or 'can_edit_messages' admin right in the channel. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.pin_chat_message
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.pin_chat_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import PinChatMessage`
- :code:`from aiogram.methods import PinChatMessage`
- :code:`from aiogram.methods.pin_chat_message import PinChatMessage`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await PinChatMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(PinChatMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return PinChatMessage(...)