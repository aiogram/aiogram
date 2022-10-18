#######################
stopMessageLiveLocation
#######################

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.stop_message_live_location
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.stop_message_live_location(...)


As message method
-----------------

.. code-block::

    result: Union[Message, bool] = await message.stop_live_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.stop_message_live_location import StopMessageLiveLocation`
- alias: :code:`from aiogram.methods import StopMessageLiveLocation`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[Message, bool] = await bot(StopMessageLiveLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return StopMessageLiveLocation(...)
