from typing import Optional

from aiogram.types import TelegramObject


class WebAppUser(TelegramObject):
    """
    This object contains the data of the Web App user.

    Source: https://core.telegram.org/bots/webapps#webappuser
    """

    id: int
    """A unique identifier for the user or bot. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. It has at most 52 significant bits, so a 64-bit integer or a double-precision float type is safe for storing this identifier."""
    is_bot: Optional[bool] = None
    """Optional. True, if this user is a bot. Returns in the receiver field only."""
    first_name: str
    """First name of the user or bot."""
    last_name: Optional[str] = None
    """Optional. Last name of the user or bot."""
    username: Optional[str] = None
    """Optional. Username of the user or bot."""
    language_code: Optional[str] = None
    """Optional. IETF language tag of the user's language. Returns in user field only."""
    photo_url: Optional[str] = None
    """Optional. URL of the user’s profile photo. The photo can be in .jpeg or .svg formats. Only returned for Web Apps launched from the attachment menu."""
