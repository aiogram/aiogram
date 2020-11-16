##############
getWebhookInfo
##############

Use this method to get current webhook status. Requires no parameters. On success, returns a WebhookInfo object. If the bot is using getUpdates, will return an object with the url field empty.

Returns: :obj:`WebhookInfo`

.. automodule:: aiogram.api.methods.get_webhook_info
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import GetWebhookInfo`
- :code:`from aiogram.api.methods import GetWebhookInfo`
- :code:`from aiogram.api.methods.get_webhook_info import GetWebhookInfo`

In handlers with current bot
----------------------------

.. code-block::

    result: WebhookInfo = await GetWebhookInfo(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: WebhookInfo = await bot(GetWebhookInfo(...))

