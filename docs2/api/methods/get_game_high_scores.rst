#################
getGameHighScores
#################

Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. On success, returns an Array of GameHighScore objects.

This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and his neighbors are not among them. Please note that this behavior is subject to change.

Returns: :obj:`List[GameHighScore]`

.. automodule:: aiogram.api.methods.get_game_high_scores
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import GetGameHighScores`
- :code:`from aiogram.api.methods import GetGameHighScores`
- :code:`from aiogram.api.methods.get_game_high_scores import GetGameHighScores`

In handlers with current bot
----------------------------

.. code-block::

    result: List[GameHighScore] = await GetGameHighScores(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: List[GameHighScore] = await bot(GetGameHighScores(...))

