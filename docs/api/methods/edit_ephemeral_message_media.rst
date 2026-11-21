#########################
editEphemeralMessageMedia
#########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_ephemeral_message_media
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_ephemeral_message_media(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_ephemeral_message_media import EditEphemeralMessageMedia`
- alias: :code:`from aiogram.methods import EditEphemeralMessageMedia`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditEphemeralMessageMedia(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditEphemeralMessageMedia(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.edit_ephemeral_media`
