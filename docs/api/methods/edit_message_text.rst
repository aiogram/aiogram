###############
editMessageText
###############

Returns: :obj:`Union[Message, bool]`

.. automodule:: aiogram.methods.edit_message_text
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Union[Message, bool] = await bot.edit_message_text(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_text import EditMessageText`
- alias: :code:`from aiogram.methods import EditMessageText`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Union[Message, bool] = await bot(EditMessageText(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageText(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.edit_text`
