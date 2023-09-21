from typing import TYPE_CHECKING, Any, Optional

from aiogram.types import TelegramObject


class WriteAccessAllowed(TelegramObject):
    """
    This object represents a service message about a user allowing a bot to write messages after adding the bot to the attachment menu or launching a Web App from a link.

    Source: https://core.telegram.org/bots/api#writeaccessallowed
    """

    web_app_name: Optional[str] = None
    """*Optional*. Name of the Web App, if the access was granted when the Web App was launched from a link"""
    from_attachment_menu: Optional[bool] = None
    """*Optional*. True, if the access was granted when the bot was added to the attachment or side menu"""
    from_request: Optional[bool] = None
    """*Optional*. True, if the access was granted after the user accepted an explicit request from a Web App sent by the method `requestWriteAccess <https://core.telegram.org/bots/webapps#initializing-mini-apps>`_"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            web_app_name: Optional[str] = None,
            from_attachment_menu: Optional[bool] = None,
            from_request: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                web_app_name=web_app_name,
                from_attachment_menu=from_attachment_menu,
                from_request=from_request,
                **__pydantic_kwargs,
            )
