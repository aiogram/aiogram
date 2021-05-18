#######################
editMessageLiveLocation
#######################

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_live_location
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_live_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_live_location import EditMessageLiveLocation`
- alias: :code:`from aiogram.methods import EditMessageLiveLocation`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Union[Message, bool] = await EditMessageLiveLocation(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[Message, bool] = await bot(EditMessageLiveLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageLiveLocation(...)
