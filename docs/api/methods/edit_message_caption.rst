##################
editMessageCaption
##################

Returns: :obj:`Message | bool`

.. automodule:: aiogram.methods.edit_message_caption
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message | bool = await bot.edit_message_caption(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_caption import EditMessageCaption`
- alias: :code:`from aiogram.methods import EditMessageCaption`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message | bool = await bot(EditMessageCaption(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageCaption(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.edit_caption`
