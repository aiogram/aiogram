#######################
editMessageLiveLocation
#######################

Returns: :obj:`Message | bool`

.. automodule:: aiogram.methods.edit_message_live_location
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message | bool = await bot.edit_message_live_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_live_location import EditMessageLiveLocation`
- alias: :code:`from aiogram.methods import EditMessageLiveLocation`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message | bool = await bot(EditMessageLiveLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageLiveLocation(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.edit_live_location`
