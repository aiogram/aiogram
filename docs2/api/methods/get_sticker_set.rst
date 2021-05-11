#############
getStickerSet
#############

Returns: :obj:`StickerSet`

.. automodule:: aiogram.methods.get_sticker_set
    :members:
    :member-order: bysource
    :undoc-members: True


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

In handlers with current bot
----------------------------

.. code-block:: python

    result: StickerSet = await GetStickerSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: StickerSet = await bot(GetStickerSet(...))
