####################
deleteChatStickerSet
####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_chat_sticker_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_chat_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_chat_sticker_set import DeleteChatStickerSet`
- alias: :code:`from aiogram.methods import DeleteChatStickerSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteChatStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteChatStickerSet(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.delete_sticker_set`
