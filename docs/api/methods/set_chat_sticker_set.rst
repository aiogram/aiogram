#################
setChatStickerSet
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_sticker_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_sticker_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_chat_sticker_set import SetChatStickerSet`
- alias: :code:`from aiogram.methods import SetChatStickerSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatStickerSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetChatStickerSet(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.set_sticker_set`
