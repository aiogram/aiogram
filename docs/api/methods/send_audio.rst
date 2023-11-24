#########
sendAudio
#########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_audio
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_audio(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_audio import SendAudio`
- alias: :code:`from aiogram.methods import SendAudio`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendAudio(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendAudio(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_audio`
- :meth:`aiogram.types.message.Message.reply_audio`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_audio`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_audio_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_audio`
