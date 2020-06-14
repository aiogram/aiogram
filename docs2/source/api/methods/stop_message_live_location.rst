#######################
stopMessageLiveLocation
#######################

Use this method to stop updating a live location message before live_period expires. On success, if the message was sent by the bot, the sent Message is returned, otherwise True is returned.

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.api.methods.stop_message_live_location
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.stop_message_live_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import StopMessageLiveLocation`
- :code:`from aiogram.api.methods import StopMessageLiveLocation`
- :code:`from aiogram.api.methods.stop_message_live_location import StopMessageLiveLocation`

In handlers with current bot
----------------------------

.. code-block::

    result: Union[Message, bool] = await StopMessageLiveLocation(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Union[Message, bool] = await bot(StopMessageLiveLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return StopMessageLiveLocation(...)