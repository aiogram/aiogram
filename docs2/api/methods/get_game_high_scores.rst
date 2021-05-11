#################
getGameHighScores
#################

Returns: :obj:`List[GameHighScore]`

.. automodule:: aiogram.methods.get_game_high_scores
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: List[GameHighScore] = await bot.get_game_high_scores(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_game_high_scores import GetGameHighScores`
- alias: :code:`from aiogram.methods import GetGameHighScores`

In handlers with current bot
----------------------------

.. code-block:: python

    result: List[GameHighScore] = await GetGameHighScores(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: List[GameHighScore] = await bot(GetGameHighScores(...))
