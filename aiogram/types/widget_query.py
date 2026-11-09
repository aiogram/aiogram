from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import AnswerWidgetQuery
    from .chat import Chat
    from .user import User
    from .widget_query_type_union import WidgetQueryTypeUnion


class WidgetQuery(TelegramObject):
    """
    This object represents an incoming query from a widget in a message sent by the bot or via the bot. Use :class:`aiogram.methods.answer_widget_query.AnswerWidgetQuery` to answer the query. Each user can send at most 5 queries per 5 seconds to the bot from all its widgets.

    Source: https://core.telegram.org/bots/api#widgetquery
    """

    id: str
    """Unique identifier for this query"""
    from_user: User = Field(..., alias="from")
    """Sender"""
    chat_instance: str
    """Global identifier, uniquely corresponding to the chat to which the message with the widget was sent"""
    type: WidgetQueryTypeUnion
    """Type of the query"""
    data: str
    """Data of the query, 1-64 bytes"""
    chat: Chat | None = None
    """*Optional*. Chat with the message containing the widget; omitted if the widget is in an inline message"""
    message_id: int | None = None
    """*Optional*. Identifier of the message containing the widget; omitted if the widget is in an inline message"""
    inline_message_id: str | None = None
    """*Optional*. Identifier of the inline message containing the widget"""
    chat_type: str | None = None
    """*Optional*. For widgets in inline messages, type of the chat to which the message was sent. Can be either 'sender' for a private chat with the inline query sender, 'private', 'group', 'supergroup', or 'channel'"""
    widget_id: str | None = None
    """*Optional*. Unique identifier of the shared widget, which sent the query; omitted if the widget isn't shared"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            from_user: User,
            chat_instance: str,
            type: WidgetQueryTypeUnion,
            data: str,
            chat: Chat | None = None,
            message_id: int | None = None,
            inline_message_id: str | None = None,
            chat_type: str | None = None,
            widget_id: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                from_user=from_user,
                chat_instance=chat_instance,
                type=type,
                data=data,
                chat=chat,
                message_id=message_id,
                inline_message_id=inline_message_id,
                chat_type=chat_type,
                widget_id=widget_id,
                **__pydantic_kwargs,
            )

    def answer(
        self,
        data: str | None = None,
        **kwargs: Any,
    ) -> AnswerWidgetQuery:
        """
        Shortcut for method :class:`aiogram.methods.answer_widget_query.AnswerWidgetQuery`
        will automatically fill method attributes:

        - :code:`widget_query_id`

        Use this method to send an answer to a query from a widget. The query must be answered within 15 seconds. The answer is received only by the widget that sent the query and doesn't change data of the widget; use :class:`aiogram.methods.edit_message_widget_data.EditMessageWidgetData` or :class:`aiogram.methods.edit_shared_widget_data.EditSharedWidgetData` to change it. On success, :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#answerwidgetquery

        :param data: Data to be returned to the widget, 0-1024 bytes
        :return: instance of method :class:`aiogram.methods.answer_widget_query.AnswerWidgetQuery`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import AnswerWidgetQuery

        return AnswerWidgetQuery(
            widget_query_id=self.id,
            data=data,
            **kwargs,
        ).as_(self._bot)
