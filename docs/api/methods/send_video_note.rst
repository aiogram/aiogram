#############
sendVideoNote
#############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_video_note
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_video_note(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_video_note import SendVideoNote`
- alias: :code:`from aiogram.methods import SendVideoNote`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendVideoNote(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendVideoNote(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_video_note`
- :meth:`aiogram.types.message.Message.reply_video_note`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_video_note`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_video_note_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_video_note`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.answer_video_note`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.reply_video_note`
