####################
deleteChatStickerSet
####################

Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.delete_chat_sticker_set
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_chat_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import DeleteChatStickerSet`
- :code:`from aiogram.api.methods import DeleteChatStickerSet`
- :code:`from aiogram.api.methods.delete_chat_sticker_set import DeleteChatStickerSet`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await DeleteChatStickerSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(DeleteChatStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return DeleteChatStickerSet(...)