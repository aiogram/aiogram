from typing import TYPE_CHECKING, Any, Optional

from aiogram.types import TelegramObject


class WriteAccessAllowed(TelegramObject):
    """
    This object represents a service message about a user allowing a bot to write messages after adding the bot to the attachment menu or launching a Web App from a link.

    Source: https://core.telegram.org/bots/api#writeaccessallowed
    """

    web_app_name: Optional[str] = None
    """*Optional*. Name of the Web App which was launched from a link"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, web_app_name: Optional[str] = None, **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(web_app_name=web_app_name, **__pydantic_kwargs)
