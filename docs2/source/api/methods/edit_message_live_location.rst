#######################
editMessageLiveLocation
#######################

Use this method to edit live location messages. A location can be edited until its live_period expires or editing is explicitly disabled by a call to stopMessageLiveLocation. On success, if the edited message was sent by the bot, the edited Message is returned, otherwise True is returned.

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.api.methods.edit_message_live_location
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_live_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import EditMessageLiveLocation`
- :code:`from aiogram.api.methods import EditMessageLiveLocation`
- :code:`from aiogram.api.methods.edit_message_live_location import EditMessageLiveLocation`

In handlers with current bot
----------------------------

.. code-block::

    result: Union[Message, bool] = await EditMessageLiveLocation(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Union[Message, bool] = await bot(EditMessageLiveLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return EditMessageLiveLocation(...)