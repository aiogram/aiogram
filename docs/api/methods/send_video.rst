#########
sendVideo
#########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_video
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_video(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_video import SendVideo`
- alias: :code:`from aiogram.methods import SendVideo`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendVideo(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendVideo(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_video`
- :meth:`aiogram.types.message.Message.reply_video`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_video`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_video_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_video`
