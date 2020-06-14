###############
addStickerToSet
###############

Use this method to add a new sticker to a set created by the bot. You must use exactly one of the fields png_sticker or tgs_sticker. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.add_sticker_to_set
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.add_sticker_to_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import AddStickerToSet`
- :code:`from aiogram.api.methods import AddStickerToSet`
- :code:`from aiogram.api.methods.add_sticker_to_set import AddStickerToSet`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await AddStickerToSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(AddStickerToSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return AddStickerToSet(...)