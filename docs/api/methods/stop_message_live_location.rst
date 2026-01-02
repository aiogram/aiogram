#######################
stopMessageLiveLocation
#######################

Returns: :obj:`Message | bool`

.. automodule:: aiogram.methods.stop_message_live_location
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message | bool = await bot.stop_message_live_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.stop_message_live_location import StopMessageLiveLocation`
- alias: :code:`from aiogram.methods import StopMessageLiveLocation`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message | bool = await bot(StopMessageLiveLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return StopMessageLiveLocation(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.stop_live_location`
