########
sendDice
########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_dice
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_dice(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_dice import SendDice`
- alias: :code:`from aiogram.methods import SendDice`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendDice(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendDice(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_dice`
- :meth:`aiogram.types.message.Message.reply_dice`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_dice`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_dice_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_dice`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.answer_dice`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.reply_dice`
