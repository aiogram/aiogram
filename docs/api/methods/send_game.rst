########
sendGame
########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_game
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.send_game import SendGame`
- alias: :code:`from aiogram.methods import SendGame`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Message = await SendGame(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendGame(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendGame(...)
