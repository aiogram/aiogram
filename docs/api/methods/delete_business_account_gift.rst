#########################
deleteBusinessAccountGift
#########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_business_account_gift
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_business_account_gift(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_business_account_gift import DeleteBusinessAccountGift`
- alias: :code:`from aiogram.methods import DeleteBusinessAccountGift`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteBusinessAccountGift(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteBusinessAccountGift(...)
