#################################
setCustomEmojiStickerSetThumbnail
#################################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_custom_emoji_sticker_set_thumbnail
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_custom_emoji_sticker_set_thumbnail(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_custom_emoji_sticker_set_thumbnail import SetCustomEmojiStickerSetThumbnail`
- alias: :code:`from aiogram.methods import SetCustomEmojiStickerSetThumbnail`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetCustomEmojiStickerSetThumbnail(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetCustomEmojiStickerSetThumbnail(...)
