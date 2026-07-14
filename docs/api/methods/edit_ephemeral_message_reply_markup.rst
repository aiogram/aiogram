###############################
editEphemeralMessageReplyMarkup
###############################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_ephemeral_message_reply_markup
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_ephemeral_message_reply_markup(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_ephemeral_message_reply_markup import EditEphemeralMessageReplyMarkup`
- alias: :code:`from aiogram.methods import EditEphemeralMessageReplyMarkup`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditEphemeralMessageReplyMarkup(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditEphemeralMessageReplyMarkup(...)
