########
sendPoll
########

Use this method to send a native poll. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_poll
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import SendPoll`
- :code:`from aiogram.methods import SendPoll`
- :code:`from aiogram.methods.send_poll import SendPoll`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendPoll(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendPoll(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendPoll(...)