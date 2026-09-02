from typing import TYPE_CHECKING, Any

from .base import TelegramMethod


class SendChatJoinRequestWebApp(TelegramMethod[bool]):
    """
    Use this method to process a received chat join request query by showing a Mini App to the user before deciding the outcome. Call :class:`aiogram.methods.answer_chat_join_request_query.AnswerChatJoinRequestQuery` to resolve the join request query based on the user interaction with the Mini App. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#sendchatjoinrequestwebapp
    """

    __returning__ = bool
    __api_method__ = "sendChatJoinRequestWebApp"

    chat_join_request_query_id: str
    """Unique identifier of the join request query"""
    web_app_url: str
    """An HTTPS URL of a Web App to be opened with additional data as specified in `Initializing Web Apps <https://core.telegram.org/bots/webapps#initializing-mini-apps>`_"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_join_request_query_id: str,
            web_app_url: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_join_request_query_id=chat_join_request_query_id,
                web_app_url=web_app_url,
                **__pydantic_kwargs,
            )
