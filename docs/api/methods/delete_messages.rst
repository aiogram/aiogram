##############
deleteMessages
##############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_messages
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_messages(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_messages import DeleteMessages`
- alias: :code:`from aiogram.methods import DeleteMessages`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteMessages(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteMessages(...)
