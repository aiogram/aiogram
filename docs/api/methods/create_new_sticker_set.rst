###################
createNewStickerSet
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.create_new_sticker_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.create_new_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.create_new_sticker_set import CreateNewStickerSet`
- alias: :code:`from aiogram.methods import CreateNewStickerSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(CreateNewStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CreateNewStickerSet(...)
