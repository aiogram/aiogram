#############
getUniqueGift
#############

Returns: :obj:`UniqueGift`

.. automodule:: aiogram.methods.get_unique_gift
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: UniqueGift = await bot.get_unique_gift(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_unique_gift import GetUniqueGift`
- alias: :code:`from aiogram.methods import GetUniqueGift`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: UniqueGift = await bot(GetUniqueGift(...))
