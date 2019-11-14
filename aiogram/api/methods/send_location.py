from typing import Any, Dict, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod


class SendLocation(TelegramMethod[Message]):
    """
    Use this method to send point on the map. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendlocation
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format @channelusername)"""

    latitude: float
    """Latitude of the location"""

    longitude: float
    """Longitude of the location"""

    live_period: Optional[int] = None
    """Period in seconds for which the location will be updated (see Live Locations, should be between 60 and 86400."""

    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""

    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""

    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="sendLocation", data=data)
