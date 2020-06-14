from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod

if TYPE_CHECKING:  # pragma: no cover
    from ..client.bot import Bot


class SendVenue(TelegramMethod[Message]):
    """
    Use this method to send information about a venue. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendvenue
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    latitude: float
    """Latitude of the venue"""
    longitude: float
    """Longitude of the venue"""
    title: str
    """Name of the venue"""
    address: str
    """Address of the venue"""
    foursquare_id: Optional[str] = None
    """Foursquare identifier of the venue"""
    foursquare_type: Optional[str] = None
    """Foursquare type of the venue, if known. (For example, 'arts_entertainment/default',
    'arts_entertainment/aquarium' or 'food/icecream'.)"""
    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an inline keyboard, custom reply
    keyboard, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="sendVenue", data=data)
