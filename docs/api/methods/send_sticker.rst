###########
sendSticker
###########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_sticker
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_sticker(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_sticker import SendSticker`
- alias: :code:`from aiogram.methods import SendSticker`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendSticker(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendSticker(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_sticker`
- :meth:`aiogram.types.message.Message.reply_sticker`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_sticker`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_sticker_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_sticker`
