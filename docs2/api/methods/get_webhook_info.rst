##############
getWebhookInfo
##############

Returns: :obj:`WebhookInfo`

.. automodule:: aiogram.methods.get_webhook_info
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: WebhookInfo = await bot.get_webhook_info(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_webhook_info import GetWebhookInfo`
- alias: :code:`from aiogram.methods import GetWebhookInfo`

In handlers with current bot
----------------------------

.. code-block:: python

    result: WebhookInfo = await GetWebhookInfo(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: WebhookInfo = await bot(GetWebhookInfo(...))
