############
getUserGifts
############

Returns: :obj:`OwnedGifts`

.. automodule:: aiogram.methods.get_user_gifts
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: OwnedGifts = await bot.get_user_gifts(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_user_gifts import GetUserGifts`
- alias: :code:`from aiogram.methods import GetUserGifts`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: OwnedGifts = await bot(GetUserGifts(...))
