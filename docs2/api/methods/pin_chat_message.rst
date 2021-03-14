##############
pinChatMessage
##############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.pin_chat_message
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.pin_chat_message import PinChatMessage`
- alias: :code:`from aiogram.methods import PinChatMessage`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await PinChatMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(PinChatMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return PinChatMessage(...)
