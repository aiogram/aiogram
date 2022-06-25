from __future__ import annotations

import datetime
from typing import List, Optional

from .base import TelegramObject


class WebhookInfo(TelegramObject):
    """
    Describes the current status of a webhook.

    Source: https://core.telegram.org/bots/api#webhookinfo
    """

    url: str
    """Webhook URL, may be empty if webhook is not set up"""
    has_custom_certificate: bool
    """:code:`True`, if a custom certificate was provided for webhook certificate checks"""
    pending_update_count: int
    """Number of updates awaiting delivery"""
    ip_address: Optional[str] = None
    """*Optional*. Currently used webhook IP address"""
    last_error_date: Optional[datetime.datetime] = None
    """*Optional*. Unix time for the most recent error that happened when trying to deliver an update via webhook"""
    last_error_message: Optional[str] = None
    """*Optional*. Error message in human-readable format for the most recent error that happened when trying to deliver an update via webhook"""
    last_synchronization_error_date: Optional[datetime.datetime] = None
    """*Optional*. Unix time of the most recent error that happened when trying to synchronize available updates with Telegram datacenters"""
    max_connections: Optional[int] = None
    """*Optional*. The maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery"""
    allowed_updates: Optional[List[str]] = None
    """*Optional*. A list of update types the bot is subscribed to. Defaults to all update types except *chat_member*"""
