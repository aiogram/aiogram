#############
getStickerSet
#############

Returns: :obj:`StickerSet`

.. automodule:: aiogram.methods.get_sticker_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: StickerSet = await bot.get_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_sticker_set import GetStickerSet`
- alias: :code:`from aiogram.methods import GetStickerSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: StickerSet = await bot(GetStickerSet(...))
