from __future__ import annotations

from typing import List, Optional

from ..types import InputFile
from .base import TelegramMethod


class SetWebhook(TelegramMethod[bool]):
    """
    Use this method to specify a URL and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified URL, containing a JSON-serialized :class:`aiogram.types.update.Update`. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns :code:`True` on success.
    If you'd like to make sure that the webhook was set by you, you can specify secret data in the parameter *secret_token*. If specified, the request will contain a header 'X-Telegram-Bot-Api-Secret-Token' with the secret token as content.

     **Notes**

     **1.** You will not be able to receive updates using :class:`aiogram.methods.get_updates.GetUpdates` for as long as an outgoing webhook is set up.

     **2.** To use a self-signed certificate, you need to upload your `public key certificate <https://core.telegram.org/bots/self-signed>`_ using *certificate* parameter. Please upload as InputFile, sending a String will not work.

     **3.** Ports currently supported *for webhooks*: **443, 80, 88, 8443**.
     If you're having any trouble setting up webhooks, please check out this `amazing guide to webhooks <https://core.telegram.org/bots/webhooks>`_.

    Source: https://core.telegram.org/bots/api#setwebhook
    """

    __returning__ = bool
    __api_method__ = "setWebhook"

    url: str
    """HTTPS URL to send updates to. Use an empty string to remove webhook integration"""
    certificate: Optional[InputFile] = None
    """Upload your public key certificate so that the root certificate in use can be checked. See our `self-signed guide <https://core.telegram.org/bots/self-signed>`_ for details."""
    ip_address: Optional[str] = None
    """The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS"""
    max_connections: Optional[int] = None
    """The maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to *40*. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput."""
    allowed_updates: Optional[List[str]] = None
    """A JSON-serialized list of the update types you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See :class:`aiogram.types.update.Update` for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used."""
    drop_pending_updates: Optional[bool] = None
    """Pass :code:`True` to drop all pending updates"""
    secret_token: Optional[str] = None
    """A secret token to be sent in a header 'X-Telegram-Bot-Api-Secret-Token' in every webhook request, 1-256 characters. Only characters :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed. The header is useful to ensure that the request comes from a webhook set by you."""
