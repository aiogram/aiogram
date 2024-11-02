######################
getCustomEmojiStickers
######################

Returns: :obj:`list[Sticker]`

.. automodule:: aiogram.methods.get_custom_emoji_stickers
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: list[Sticker] = await bot.get_custom_emoji_stickers(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_custom_emoji_stickers import GetCustomEmojiStickers`
- alias: :code:`from aiogram.methods import GetCustomEmojiStickers`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: list[Sticker] = await bot(GetCustomEmojiStickers(...))
