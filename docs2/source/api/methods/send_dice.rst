########
sendDice
########

Use this method to send an animated emoji that will display a random value. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_dice
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_dice(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendDice`
- :code:`from aiogram.api.methods import SendDice`
- :code:`from aiogram.api.methods.send_dice import SendDice`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendDice(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendDice(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendDice(...)