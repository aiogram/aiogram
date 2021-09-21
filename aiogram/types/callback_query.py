from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import AnswerCallbackQuery
    from .message import Message
    from .user import User


class CallbackQuery(TelegramObject):
    """
    This object represents an incoming callback query from a callback button in an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_. If the button that originated the query was attached to a message sent by the bot, the field *message* will be present. If the button was attached to a message sent via the bot (in `inline mode <https://core.telegram.org/bots/api#inline-mode>`_), the field *inline_message_id* will be present. Exactly one of the fields *data* or *game_short_name* will be present.

     **NOTE:** After the user presses a callback button, Telegram clients will display a progress bar until you call :class:`aiogram.methods.answer_callback_query.AnswerCallbackQuery`. It is, therefore, necessary to react by calling :class:`aiogram.methods.answer_callback_query.AnswerCallbackQuery` even if no notification to the user is needed (e.g., without specifying any of the optional parameters).

    Source: https://core.telegram.org/bots/api#callbackquery
    """

    id: str
    """Unique identifier for this query"""
    from_user: User = Field(..., alias="from")
    """Sender"""
    chat_instance: str
    """Global identifier, uniquely corresponding to the chat to which the message with the callback button was sent. Useful for high scores in :class:`aiogram.methods.games.Games`."""
    message: Optional[Message] = None
    """*Optional*. Message with the callback button that originated the query. Note that message content and message date will not be available if the message is too old"""
    inline_message_id: Optional[str] = None
    """*Optional*. Identifier of the message sent via the bot in inline mode, that originated the query."""
    data: Optional[str] = None
    """*Optional*. Data associated with the callback button. Be aware that a bad client can send arbitrary data in this field."""
    game_short_name: Optional[str] = None
    """*Optional*. Short name of a `Game <https://core.telegram.org/bots/api#games>`_ to be returned, serves as the unique identifier for the game"""

    def answer(
        self,
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ) -> AnswerCallbackQuery:
        """
        Answer to callback query

        :param text:
        :param show_alert:
        :param url:
        :param cache_time:
        :return:
        """
        from ..methods import AnswerCallbackQuery

        return AnswerCallbackQuery(
            callback_query_id=self.id,
            text=text,
            show_alert=show_alert,
            url=url,
            cache_time=cache_time,
        )
