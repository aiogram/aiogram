#############
deleteWebhook
#############

Use this method to remove webhook integration if you decide to switch back to getUpdates. Returns True on success. Requires no parameters.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.delete_webhook
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_webhook(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import DeleteWebhook`
- :code:`from aiogram.api.methods import DeleteWebhook`
- :code:`from aiogram.api.methods.delete_webhook import DeleteWebhook`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await DeleteWebhook(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(DeleteWebhook(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return DeleteWebhook(...)