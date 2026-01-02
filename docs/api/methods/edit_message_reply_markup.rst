######################
editMessageReplyMarkup
######################

Returns: :obj:`Message | bool`

.. automodule:: aiogram.methods.edit_message_reply_markup
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message | bool = await bot.edit_message_reply_markup(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_reply_markup import EditMessageReplyMarkup`
- alias: :code:`from aiogram.methods import EditMessageReplyMarkup`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message | bool = await bot(EditMessageReplyMarkup(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageReplyMarkup(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.edit_reply_markup`
- :meth:`aiogram.types.message.Message.delete_reply_markup`
