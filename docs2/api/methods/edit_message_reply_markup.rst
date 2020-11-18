######################
editMessageReplyMarkup
######################

Use this method to edit only the reply markup of messages. On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_reply_markup
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_reply_markup(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import EditMessageReplyMarkup`
- :code:`from aiogram.methods import EditMessageReplyMarkup`
- :code:`from aiogram.methods.edit_message_reply_markup import EditMessageReplyMarkup`

In handlers with current bot
----------------------------

.. code-block::

    result: Union[Message, bool] = await EditMessageReplyMarkup(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Union[Message, bool] = await bot(EditMessageReplyMarkup(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return EditMessageReplyMarkup(...)