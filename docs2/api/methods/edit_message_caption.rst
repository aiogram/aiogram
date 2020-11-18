##################
editMessageCaption
##################

Use this method to edit captions of messages. On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_caption
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_caption(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import EditMessageCaption`
- :code:`from aiogram.methods import EditMessageCaption`
- :code:`from aiogram.methods.edit_message_caption import EditMessageCaption`

In handlers with current bot
----------------------------

.. code-block::

    result: Union[Message, bool] = await EditMessageCaption(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Union[Message, bool] = await bot(EditMessageCaption(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return EditMessageCaption(...)