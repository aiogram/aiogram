###############
editMessageText
###############

Use this method to edit text and game messages. On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.api.methods.edit_message_text
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_text(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import EditMessageText`
- :code:`from aiogram.api.methods import EditMessageText`
- :code:`from aiogram.api.methods.edit_message_text import EditMessageText`

In handlers with current bot
----------------------------

.. code-block::

    result: Union[Message, bool] = await EditMessageText(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Union[Message, bool] = await bot(EditMessageText(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return EditMessageText(...)