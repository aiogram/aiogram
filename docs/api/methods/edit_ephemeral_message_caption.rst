###########################
editEphemeralMessageCaption
###########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_ephemeral_message_caption
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_ephemeral_message_caption(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_ephemeral_message_caption import EditEphemeralMessageCaption`
- alias: :code:`from aiogram.methods import EditEphemeralMessageCaption`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditEphemeralMessageCaption(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditEphemeralMessageCaption(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.edit_ephemeral_caption`
