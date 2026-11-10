from typing import TYPE_CHECKING, Any

from .base import TelegramMethod


class AnswerWidgetQuery(TelegramMethod[bool]):
    """
    Use this method to send an answer to a query from a widget. The query must be answered within 15 seconds. The answer is received only by the widget that sent the query and doesn't change data of the widget; use :class:`aiogram.methods.edit_message_widget_data.EditMessageWidgetData` or :class:`aiogram.methods.edit_shared_widget_data.EditSharedWidgetData` to change it. On success, :code:`True` is returned.

    Source: https://core.telegram.org/bots/api#answerwidgetquery
    """

    __returning__ = bool
    __api_method__ = "answerWidgetQuery"

    widget_query_id: str
    """Unique identifier for the query to be answered"""
    data: str | None = None
    """Data to be returned to the widget, 0-1024 bytes"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            widget_query_id: str,
            data: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(widget_query_id=widget_query_id, data=data, **__pydantic_kwargs)
