############
transferGift
############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.transfer_gift
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.transfer_gift(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.transfer_gift import TransferGift`
- alias: :code:`from aiogram.methods import TransferGift`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(TransferGift(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return TransferGift(...)
