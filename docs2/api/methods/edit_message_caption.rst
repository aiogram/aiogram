##################
editMessageCaption
##################

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_caption
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.edit_message_caption import EditMessageCaption`
- alias: :code:`from aiogram.methods import EditMessageCaption`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Union[Message, bool] = await EditMessageCaption(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[Message, bool] = await bot(EditMessageCaption(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageCaption(...)