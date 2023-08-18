from typing import TYPE_CHECKING, Any, Union

from aiogram.methods import TelegramMethod


class UnpinAllGeneralForumTopicMessages(TelegramMethod[bool]):
    """
    Use this method to clear the list of pinned messages in a General forum topic. The bot must be an administrator in the chat for this to work and must have the *can_pin_messages* administrator right in the supergroup. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#unpinallgeneralforumtopicmessages
    """

    __returning__ = bool
    __api_method__ = "unpinAllGeneralForumTopicMessages"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, chat_id: Union[int, str], **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(chat_id=chat_id, **__pydantic_kwargs)
