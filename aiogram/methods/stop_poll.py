from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..types import InlineKeyboardMarkup, Poll
from .base import TelegramMethod


class StopPoll(TelegramMethod[Poll]):
    """
    Use this method to stop a poll which was sent by the bot. On success, the stopped :class:`aiogram.types.poll.Poll` is returned.

    Source: https://core.telegram.org/bots/api#stoppoll
    """

    __returning__ = Poll
    __api_method__ = "stopPoll"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: int
    """Identifier of the original message with the poll"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for a new message `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            message_id: int,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
