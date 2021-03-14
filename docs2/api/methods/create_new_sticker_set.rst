###################
createNewStickerSet
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.create_new_sticker_set
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.create_new_sticker_set import CreateNewStickerSet`
- alias: :code:`from aiogram.methods import CreateNewStickerSet`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await CreateNewStickerSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(CreateNewStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CreateNewStickerSet(...)
