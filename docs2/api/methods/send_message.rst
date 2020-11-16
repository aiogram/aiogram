###########
sendMessage
###########

Use this method to send text messages. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_message
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendMessage`
- :code:`from aiogram.api.methods import SendMessage`
- :code:`from aiogram.api.methods.send_message import SendMessage`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendMessage(...)