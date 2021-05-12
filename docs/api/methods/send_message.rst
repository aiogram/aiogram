###########
sendMessage
###########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_message
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.send_message import SendMessage`
- alias: :code:`from aiogram.methods import SendMessage`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Message = await SendMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendMessage(...)
