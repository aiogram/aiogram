######################
setStickerMaskPosition
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_sticker_mask_position
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_sticker_mask_position(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_sticker_mask_position import SetStickerMaskPosition`
- alias: :code:`from aiogram.methods import SetStickerMaskPosition`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetStickerMaskPosition(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetStickerMaskPosition(...)
