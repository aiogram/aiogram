###################
getStarTransactions
###################

Returns: :obj:`StarTransactions`

.. automodule:: aiogram.methods.get_star_transactions
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: StarTransactions = await bot.get_star_transactions(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_star_transactions import GetStarTransactions`
- alias: :code:`from aiogram.methods import GetStarTransactions`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: StarTransactions = await bot(GetStarTransactions(...))
