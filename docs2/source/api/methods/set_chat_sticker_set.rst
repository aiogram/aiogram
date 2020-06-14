#################
setChatStickerSet
#################

Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_chat_sticker_set
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetChatStickerSet`
- :code:`from aiogram.api.methods import SetChatStickerSet`
- :code:`from aiogram.api.methods.set_chat_sticker_set import SetChatStickerSet`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetChatStickerSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetChatStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetChatStickerSet(...)