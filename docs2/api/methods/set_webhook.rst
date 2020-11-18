##########
setWebhook
##########

Use this method to specify a url and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified url, containing a JSON-serialized Update. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns True on success.

If you'd like to make sure that the Webhook request comes from Telegram, we recommend using a secret path in the URL, e.g. https://www.example.com/<token>. Since nobody else knows your bot's token, you can be pretty sure it's us.

Notes

1. You will not be able to receive updates using getUpdates for as long as an outgoing webhook is set up.

2. To use a self-signed certificate, you need to upload your public key certificate using certificate parameter. Please upload as InputFile, sending a String will not work.

3. Ports currently supported for Webhooks: 443, 80, 88, 8443.

NEW! If you're having any trouble setting up webhooks, please check out this amazing guide to Webhooks.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_webhook
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import SetWebhook`
- :code:`from aiogram.methods import SetWebhook`
- :code:`from aiogram.methods.set_webhook import SetWebhook`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetWebhook(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetWebhook(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetWebhook(...)