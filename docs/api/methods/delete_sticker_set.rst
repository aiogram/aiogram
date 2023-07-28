################
deleteStickerSet
################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_sticker_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_sticker_set import DeleteStickerSet`
- alias: :code:`from aiogram.methods import DeleteStickerSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteStickerSet(...)
