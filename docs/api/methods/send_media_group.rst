##############
sendMediaGroup
##############

Returns: :obj:`List[Message]`

.. automodule:: aiogram.methods.send_media_group
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: List[Message] = await bot.send_media_group(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_media_group import SendMediaGroup`
- alias: :code:`from aiogram.methods import SendMediaGroup`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: List[Message] = await bot(SendMediaGroup(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendMediaGroup(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_media_group`
- :meth:`aiogram.types.message.Message.reply_media_group`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_media_group`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_media_group_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_media_group`
