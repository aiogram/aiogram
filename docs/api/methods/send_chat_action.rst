##############
sendChatAction
##############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.send_chat_action
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.send_chat_action(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_chat_action import SendChatAction`
- alias: :code:`from aiogram.methods import SendChatAction`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SendChatAction(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendChatAction(...)
