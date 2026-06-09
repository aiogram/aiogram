######################
deleteBusinessMessages
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_business_messages
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_business_messages(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_business_messages import DeleteBusinessMessages`
- alias: :code:`from aiogram.methods import DeleteBusinessMessages`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteBusinessMessages(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteBusinessMessages(...)
