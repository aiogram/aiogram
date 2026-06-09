#######################
getBusinessAccountGifts
#######################

Returns: :obj:`OwnedGifts`

.. automodule:: aiogram.methods.get_business_account_gifts
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: OwnedGifts = await bot.get_business_account_gifts(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_business_account_gifts import GetBusinessAccountGifts`
- alias: :code:`from aiogram.methods import GetBusinessAccountGifts`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: OwnedGifts = await bot(GetBusinessAccountGifts(...))
