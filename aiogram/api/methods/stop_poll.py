from typing import Any, Dict, Optional, Union

from ..types import InlineKeyboardMarkup, Poll
from .base import Request, TelegramMethod


class StopPoll(TelegramMethod[Poll]):
    """
    Use this method to stop a poll which was sent by the bot. On success, the stopped Poll with
    the final results is returned.

    Source: https://core.telegram.org/bots/api#stoppoll
    """

    __returning__ = Poll

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    message_id: int
    """Identifier of the original message with the poll"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for a new message inline keyboard."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="stopPoll", data=data)
