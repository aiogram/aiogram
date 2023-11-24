############
sendLocation
############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_location
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_location import SendLocation`
- alias: :code:`from aiogram.methods import SendLocation`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendLocation(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_location`
- :meth:`aiogram.types.message.Message.reply_location`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_location`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_location_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_location`
