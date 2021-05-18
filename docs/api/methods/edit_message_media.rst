################
editMessageMedia
################

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_media
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_media(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_media import EditMessageMedia`
- alias: :code:`from aiogram.methods import EditMessageMedia`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Union[Message, bool] = await EditMessageMedia(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[Message, bool] = await bot(EditMessageMedia(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageMedia(...)
