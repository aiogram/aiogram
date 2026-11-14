from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import AnswerWidgetQuery
    from .user import User
    from .widget_query_type_union import WidgetQueryTypeUnion


class SharedWidgetQuery(TelegramObject):
    """
    This object represents an incoming query from a forwarded message with a shared widget created by the bot. Use :class:`aiogram.methods.answer_widget_query.AnswerWidgetQuery` to answer the query. Each user can send at most 5 queries per 5 seconds to the bot from all its widgets.

    Source: https://core.telegram.org/bots/api#sharedwidgetquery
    """

    id: str
    """Unique identifier for this query"""
    from_user: User = Field(..., alias="from")
    """Sender"""
    type: WidgetQueryTypeUnion
    """Type of the query"""
    data: str
    """Data of the query, 1-64 bytes"""
    widget_id: str
    """Unique identifier of the shared widget, which sent the query"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            from_user: User,
            type: WidgetQueryTypeUnion,
            data: str,
            widget_id: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                from_user=from_user,
                type=type,
                data=data,
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
