from __future__ import annotations

from .base import TelegramObject


class WebAppInfo(TelegramObject):
    """
    Describes a `Web App <https://core.telegram.org/bots/webapps>`_.

    Source: https://core.telegram.org/bots/api#webappinfo
    """

    url: str
    """An HTTPS URL of a Web App to be opened with additional data as specified in `Initializing Web Apps <https://core.telegram.org/bots/webapps#initializing-web-apps>`_"""
