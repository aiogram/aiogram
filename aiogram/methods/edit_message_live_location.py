from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import InlineKeyboardMarkup, Message
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class EditMessageLiveLocation(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit live location messages. A location can be edited until its *live_period* expires or editing is explicitly disabled by a call to :class:`aiogram.methods.stop_message_live_location.StopMessageLiveLocation`. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

    Source: https://core.telegram.org/bots/api#editmessagelivelocation
    """

    __returning__ = Union[Message, bool]

    latitude: float
    """Latitude of new location"""
    longitude: float
    """Longitude of new location"""
    chat_id: Optional[Union[int, str]] = None
    """Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Identifier of the message to edit"""
    inline_message_id: Optional[str] = None
    """Required if *chat_id* and *message_id* are not specified. Identifier of the inline message"""
    horizontal_accuracy: Optional[float] = None
    """The radius of uncertainty for the location, measured in meters; 0-1500"""
    heading: Optional[int] = None
    """Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified."""
    proximity_alert_radius: Optional[int] = None
    """The maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="editMessageLiveLocation", data=data)
