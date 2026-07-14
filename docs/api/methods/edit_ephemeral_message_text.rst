########################
editEphemeralMessageText
########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_ephemeral_message_text
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_ephemeral_message_text(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_ephemeral_message_text import EditEphemeralMessageText`
- alias: :code:`from aiogram.methods import EditEphemeralMessageText`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditEphemeralMessageText(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditEphemeralMessageText(...)
