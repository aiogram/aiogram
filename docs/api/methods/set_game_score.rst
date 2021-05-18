############
setGameScore
############

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.set_game_score
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.set_game_score(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_game_score import SetGameScore`
- alias: :code:`from aiogram.methods import SetGameScore`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Union[Message, bool] = await SetGameScore(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[Message, bool] = await bot(SetGameScore(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetGameScore(...)
