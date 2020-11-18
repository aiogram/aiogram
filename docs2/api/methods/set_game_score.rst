############
setGameScore
############

Use this method to set the score of the specified user in a game. On success, if the message was sent by the bot, returns the edited Message, otherwise returns True. Returns an error, if the new score is not greater than the user's current score in the chat and force is False.

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.set_game_score
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import SetGameScore`
- :code:`from aiogram.methods import SetGameScore`
- :code:`from aiogram.methods.set_game_score import SetGameScore`

In handlers with current bot
----------------------------

.. code-block::

    result: Union[Message, bool] = await SetGameScore(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Union[Message, bool] = await bot(SetGameScore(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetGameScore(...)