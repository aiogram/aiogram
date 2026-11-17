####################
editSharedWidgetData
####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.edit_shared_widget_data
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.edit_shared_widget_data(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_shared_widget_data import EditSharedWidgetData`
- alias: :code:`from aiogram.methods import EditSharedWidgetData`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(EditSharedWidgetData(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditSharedWidgetData(...)
