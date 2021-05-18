########
sendPoll
########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_poll
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_poll(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_poll import SendPoll`
- alias: :code:`from aiogram.methods import SendPoll`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Message = await SendPoll(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendPoll(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendPoll(...)
