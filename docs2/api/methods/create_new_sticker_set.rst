###################
createNewStickerSet
###################

Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You must use exactly one of the fields png_sticker or tgs_sticker. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.create_new_sticker_set
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.create_new_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import CreateNewStickerSet`
- :code:`from aiogram.api.methods import CreateNewStickerSet`
- :code:`from aiogram.api.methods.create_new_sticker_set import CreateNewStickerSet`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await CreateNewStickerSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(CreateNewStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return CreateNewStickerSet(...)