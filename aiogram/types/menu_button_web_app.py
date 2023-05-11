from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from ..enums import MenuButtonType
from .menu_button import MenuButton
from .web_app_info import WebAppInfo


class MenuButtonWebApp(MenuButton, kw_only=True):
    """
    Represents a menu button, which launches a `Web App <https://core.telegram.org/bots/webapps>`_.

    Source: https://core.telegram.org/bots/api#menubuttonwebapp
    """

    type: str = msgspec.field(default_factory=lambda: MenuButtonType.WEB_APP)
    """Type of the button, must be *web_app*"""
    text: str
    """Text on the button"""
    web_app: WebAppInfo
    """Description of the Web App that will be launched when the user presses the button. The Web App will be able to send an arbitrary message on behalf of the user using the method :class:`aiogram.methods.answer_web_app_query.AnswerWebAppQuery`."""
