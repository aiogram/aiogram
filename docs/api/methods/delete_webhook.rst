#############
deleteWebhook
#############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_webhook
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_webhook(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_webhook import DeleteWebhook`
- alias: :code:`from aiogram.methods import DeleteWebhook`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteWebhook(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteWebhook(...)
