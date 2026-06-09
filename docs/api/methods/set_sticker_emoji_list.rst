###################
setStickerEmojiList
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_sticker_emoji_list
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_sticker_emoji_list(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_sticker_emoji_list import SetStickerEmojiList`
- alias: :code:`from aiogram.methods import SetStickerEmojiList`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetStickerEmojiList(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetStickerEmojiList(...)
