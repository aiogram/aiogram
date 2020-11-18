########
sendGame
########

Use this method to send a game. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_game
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_game(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendGame`
- :code:`from aiogram.methods import SendGame`
- :code:`from aiogram.methods.send_game import SendGame`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendGame(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendGame(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendGame(...)