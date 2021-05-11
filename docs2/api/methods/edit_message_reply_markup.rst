######################
editMessageReplyMarkup
######################

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_reply_markup
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.edit_message_reply_markup import EditMessageReplyMarkup`
- alias: :code:`from aiogram.methods import EditMessageReplyMarkup`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Union[Message, bool] = await EditMessageReplyMarkup(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[Message, bool] = await bot(EditMessageReplyMarkup(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageReplyMarkup(...)
