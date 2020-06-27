####################
deleteStickerFromSet
####################

Use this method to delete a sticker from a set created by the bot. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.delete_sticker_from_set
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_sticker_from_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import DeleteStickerFromSet`
- :code:`from aiogram.api.methods import DeleteStickerFromSet`
- :code:`from aiogram.api.methods.delete_sticker_from_set import DeleteStickerFromSet`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await DeleteStickerFromSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(DeleteStickerFromSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return DeleteStickerFromSet(...)