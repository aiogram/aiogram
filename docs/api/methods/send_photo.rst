#########
sendPhoto
#########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_photo
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_photo import SendPhoto`
- alias: :code:`from aiogram.methods import SendPhoto`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendPhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendPhoto(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_photo`
- :meth:`aiogram.types.message.Message.reply_photo`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_photo`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_photo_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_photo`
