from typing import TYPE_CHECKING, Any, List, Union

from .base import TelegramMethod


class DeleteMessages(TelegramMethod[bool]):
    """
    Use this method to delete multiple messages simultaneously. If some of the specified messages can't be found, they are skipped. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#deletemessages
    """

    __returning__ = bool
    __api_method__ = "deleteMessages"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_ids: List[int]
    """Identifiers of 1-100 messages to delete. See :class:`aiogram.methods.delete_message.DeleteMessage` for limitations on which messages can be deleted"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            message_ids: List[int],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(chat_id=chat_id, message_ids=message_ids, **__pydantic_kwargs)
