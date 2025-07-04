################
getMyStarBalance
################

Returns: :obj:`StarAmount`

.. automodule:: aiogram.methods.get_my_star_balance
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: StarAmount = await bot.get_my_star_balance(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_my_star_balance import GetMyStarBalance`
- alias: :code:`from aiogram.methods import GetMyStarBalance`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: StarAmount = await bot(GetMyStarBalance(...))
