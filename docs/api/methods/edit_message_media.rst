################
editMessageMedia
################

Returns: :obj:`Message | bool`

.. automodule:: aiogram.methods.edit_message_media
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message | bool = await bot.edit_message_media(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_media import EditMessageMedia`
- alias: :code:`from aiogram.methods import EditMessageMedia`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message | bool = await bot(EditMessageMedia(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageMedia(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.edit_media`
