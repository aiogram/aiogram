####################
editMessageChecklist
####################

Returns: :obj:`Message`

.. automodule:: aiogram.methods.edit_message_checklist
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.edit_message_checklist(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_message_checklist import EditMessageChecklist`
- alias: :code:`from aiogram.methods import EditMessageChecklist`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(EditMessageChecklist(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditMessageChecklist(...)
