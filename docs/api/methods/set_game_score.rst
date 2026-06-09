############
setGameScore
############

Returns: :obj:`Message | bool`

.. automodule:: aiogram.methods.set_game_score
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message | bool = await bot.set_game_score(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_game_score import SetGameScore`
- alias: :code:`from aiogram.methods import SetGameScore`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message | bool = await bot(SetGameScore(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetGameScore(...)
