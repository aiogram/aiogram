##########
setWebhook
##########

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_webhook
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_webhook(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_webhook import SetWebhook`
- alias: :code:`from aiogram.methods import SetWebhook`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await SetWebhook(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetWebhook(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetWebhook(...)