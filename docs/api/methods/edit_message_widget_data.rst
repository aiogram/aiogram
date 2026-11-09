#####################
editMessageWidgetData
#####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_message_widget_data
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_message_widget_data(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_widget_data import EditMessageWidgetData`
- alias: :code:`from aiogram.methods import EditMessageWidgetData`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditMessageWidgetData(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageWidgetData(...)
