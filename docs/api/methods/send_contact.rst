###########
sendContact
###########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_contact
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_contact(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_contact import SendContact`
- alias: :code:`from aiogram.methods import SendContact`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendContact(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendContact(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_contact`
- :meth:`aiogram.types.message.Message.reply_contact`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_contact`
- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.answer_contact_pm`
- :meth:`aiogram.types.chat_member_updated.ChatMemberUpdated.answer_contact`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.answer_contact`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.reply_contact`
