####################
deleteChatStickerSet
####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_chat_sticker_set
    :members:
    :member-order: bysource
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
