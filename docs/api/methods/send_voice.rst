#########
sendVoice
#########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_voice
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_voice(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_voice import SendVoice`
- alias: :code:`from aiogram.methods import SendVoice`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendVoice(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendVoice(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_voice`
- :meth:`aiogram.types.message.Message.reply_voice`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_voice`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_voice_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_voice`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.answer_voice`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.reply_voice`
