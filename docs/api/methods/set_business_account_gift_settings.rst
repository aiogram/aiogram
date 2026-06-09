##############################
setBusinessAccountGiftSettings
##############################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_business_account_gift_settings
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_business_account_gift_settings(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_business_account_gift_settings import SetBusinessAccountGiftSettings`
- alias: :code:`from aiogram.methods import SetBusinessAccountGiftSettings`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetBusinessAccountGiftSettings(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetBusinessAccountGiftSettings(...)
