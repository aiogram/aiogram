########
sendPoll
########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_poll
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_poll(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_poll import SendPoll`
- alias: :code:`from aiogram.methods import SendPoll`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendPoll(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendPoll(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_poll`
- :meth:`aiogram.types.message.Message.reply_poll`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_poll`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_poll_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_poll`
