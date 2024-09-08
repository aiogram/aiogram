########
sendGame
########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_game
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_game(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_game import SendGame`
- alias: :code:`from aiogram.methods import SendGame`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendGame(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendGame(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_game`
- :meth:`aiogram.types.message.Message.reply_game`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_game`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_game_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_game`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.answer_game`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.reply_game`
