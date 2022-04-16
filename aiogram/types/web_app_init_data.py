from typing import Optional

from aiogram.types import TelegramObject
from aiogram.types.web_app_user import WebAppUser


class WebAppInitData(TelegramObject):
    query_id: Optional[str] = None
    """Optional. A unique identifier for the Web App session, required for sending messages via the answerWebAppQuery method."""
    user: Optional[WebAppUser] = None
    """Optional. An object containing data about the current user."""
    receiver: Optional[WebAppUser] = None
    """Optional. An object containing data about the chat partner of the current user in the chat where the bot was launched via the attachment menu. Returned only for Web Apps launched via the attachment menu."""
    start_param: Optional[str] = None
    """Optional. The value of the startattach parameter, passed via link. Only returned for Web Apps when launched from the attachment menu via link. The value of the start_param parameter will also be passed in the GET-parameter tgWebAppStartParam, so the Web App can load the correct interface right away."""
    auth_date: int
    """Unix time when the form was opened."""
    hash: str
    """A hash of all passed parameters, which the bot server can use to check their validity."""
