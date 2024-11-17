#################
getAvailableGifts
#################

Returns: :obj:`Gifts`

.. automodule:: aiogram.methods.get_available_gifts
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Gifts = await bot.get_available_gifts(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_available_gifts import GetAvailableGifts`
- alias: :code:`from aiogram.methods import GetAvailableGifts`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Gifts = await bot(GetAvailableGifts(...))
