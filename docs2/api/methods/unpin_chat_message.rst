################
unpinChatMessage
################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.unpin_chat_message
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.unpin_chat_message import UnpinChatMessage`
- alias: :code:`from aiogram.methods import UnpinChatMessage`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await UnpinChatMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(UnpinChatMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return UnpinChatMessage(...)
