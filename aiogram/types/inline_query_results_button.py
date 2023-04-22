from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .web_app_info import WebAppInfo


class InlineQueryResultsButton(TelegramObject):
    """
    This object represents a button to be shown above inline query results. You **must** use exactly one of the optional fields.

    Source: https://core.telegram.org/bots/api#inlinequeryresultsbutton
    """

    text: str
    """Label text on the button"""
    web_app: Optional[WebAppInfo] = None
    """*Optional*. Description of the `Web App <https://core.telegram.org/bots/webapps>`_ that will be launched when the user presses the button. The Web App will be able to switch back to the inline mode using the method *web_app_switch_inline_query* inside the Web App."""
    start_parameter: Optional[str] = None
    """*Optional*. `Deep-linking <https://core.telegram.org/bots/features#deep-linking>`_ parameter for the /start message sent to the bot when a user presses the button. 1-64 characters, only :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed."""
