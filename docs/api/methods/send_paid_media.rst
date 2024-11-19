#############
sendPaidMedia
#############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_paid_media
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_paid_media(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_paid_media import SendPaidMedia`
- alias: :code:`from aiogram.methods import SendPaidMedia`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendPaidMedia(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendPaidMedia(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_paid_media`
- :meth:`aiogram.types.message.Message.reply_paid_media`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.answer_paid_media`
- :meth:`aiogram.types.inaccessible_message.InaccessibleMessage.reply_paid_media`
