from typing import Any, Dict, List, Optional

from .base import Request, TelegramMethod
from ..types import InputFile


class SetWebhook(TelegramMethod[bool]):
    """
    Use this method to specify a url and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified url, containing a JSON-serialized Update. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns True on success.
    If you'd like to make sure that the Webhook request comes from Telegram, we recommend using a secret path in the URL, e.g. https://www.example.com/<token>. Since nobody else knows your bot‘s token, you can be pretty sure it’s us.
    Notes
    1. You will not be able to receive updates using getUpdates for as long as an outgoing webhook is set up.
    2. To use a self-signed certificate, you need to upload your public key certificate using certificate parameter. Please upload as InputFile, sending a String will not work.
    3. Ports currently supported for Webhooks: 443, 80, 88, 8443.
    NEW! If you're having any trouble setting up webhooks, please check out this amazing guide to Webhooks.

    Source: https://core.telegram.org/bots/api#setwebhook
    """

    __returning__ = bool

    url: str
    """HTTPS url to send updates to. Use an empty string to remove webhook integration"""

    certificate: Optional[InputFile] = None
    """Upload your public key certificate so that the root certificate in use can be checked. See our self-signed guide for details."""

    max_connections: Optional[int] = None
    """Maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to 40. Use lower values to limit the load on your bot‘s server, and higher values to increase your bot’s throughput."""

    allowed_updates: Optional[List[str]] = None
    """List the types of updates you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). If not specified, the previous setting will be used.

    Please note that this parameter doesn't affect updates created before the call to the setWebhook, so unwanted updates may be received for a short period of time."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={"certificate"})

        files: Dict[str, Any] = {}
        self.prepare_file(data=data, files=files, name="certificate", value=self.certificate)

        return Request(method="setWebhook", data=data, files=files)
