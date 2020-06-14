#############
getStickerSet
#############

Use this method to get a sticker set. On success, a StickerSet object is returned.

Returns: :obj:`StickerSet`

.. automodule:: aiogram.api.methods.get_sticker_set
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: StickerSet = await bot.get_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetStickerSet`
- :code:`from aiogram.api.methods import GetStickerSet`
- :code:`from aiogram.api.methods.get_sticker_set import GetStickerSet`

In handlers with current bot
----------------------------

.. code-block::

    result: StickerSet = await GetStickerSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: StickerSet = await bot(GetStickerSet(...))

