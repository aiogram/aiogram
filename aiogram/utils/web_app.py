import hashlib
import hmac
import json
from datetime import datetime
from operator import itemgetter
from typing import Any, Callable, Optional
from urllib.parse import parse_qsl

from aiogram.types import TelegramObject


class WebAppUser(TelegramObject):
    """
    This object contains the data of the Web App user.

    Source: https://core.telegram.org/bots/webapps#webappuser
    """

    id: int
    """A unique identifier for the user or bot. This number may have more than 32 significant bits
    and some programming languages may have difficulty/silent defects in interpreting it.
    It has at most 52 significant bits, so a 64-bit integer or a double-precision float type
    is safe for storing this identifier."""
    is_bot: Optional[bool] = None
    """True, if this user is a bot. Returns in the receiver field only."""
    first_name: str
    """First name of the user or bot."""
    last_name: Optional[str] = None
    """Last name of the user or bot."""
    username: Optional[str] = None
    """Username of the user or bot."""
    language_code: Optional[str] = None
    """IETF language tag of the user's language. Returns in user field only."""
    photo_url: Optional[str] = None
    """URL of the user’s profile photo. The photo can be in .jpeg or .svg formats.
    Only returned for Web Apps launched from the attachment menu."""


class WebAppInitData(TelegramObject):
    """
    This object contains data that is transferred to the Web App when it is opened.
    It is empty if the Web App was launched from a keyboard button.

    Source: https://core.telegram.org/bots/webapps#webappinitdata
    """

    query_id: Optional[str] = None
    """A unique identifier for the Web App session, required for sending messages
    via the answerWebAppQuery method."""
    user: Optional[WebAppUser] = None
    """An object containing data about the current user."""
    receiver: Optional[WebAppUser] = None
    """An object containing data about the chat partner of the current user in the chat where
    the bot was launched via the attachment menu.
    Returned only for Web Apps launched via the attachment menu."""
    start_param: Optional[str] = None
    """The value of the startattach parameter, passed via link.
    Only returned for Web Apps when launched from the attachment menu via link.
    The value of the start_param parameter will also be passed in the GET-parameter
    tgWebAppStartParam, so the Web App can load the correct interface right away."""
    auth_date: datetime
    """Unix time when the form was opened."""
    hash: str
    """A hash of all passed parameters, which the bot server can use to check their validity."""


def check_webapp_signature(token: str, init_data: str) -> bool:
    """
    Check incoming WebApp init data signature

    Source: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

    :param token: bot Token
    :param init_data: data from frontend to be validated
    :return:
    """
    try:
        parsed_data = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:  # pragma: no cover
        # Init data is not a valid query string
        return False
    if "hash" not in parsed_data:
        # Hash is not present in init data
        return False
    hash_ = parsed_data.pop("hash")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    secret_key = hmac.new(key=b"WebAppData", msg=token.encode(), digestmod=hashlib.sha256)
    calculated_hash = hmac.new(
        key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    return calculated_hash == hash_


def parse_webapp_init_data(
    init_data: str,
    *,
    loads: Callable[..., Any] = json.loads,
) -> WebAppInitData:
    """
    Parse WebApp init data and return it as WebAppInitData object

    This method doesn't make any security check, so you shall not trust to this data,
    use :code:`safe_parse_webapp_init_data` instead.

    :param init_data: data from frontend to be parsed
    :param loads:
    :return:
    """
    result = {}
    for key, value in parse_qsl(init_data):
        if (value.startswith("[") and value.endswith("]")) or (
            value.startswith("{") and value.endswith("}")
        ):
            value = loads(value)
        result[key] = value
    return WebAppInitData(**result)


def safe_parse_webapp_init_data(
    token: str,
    init_data: str,
    *,
    loads: Callable[..., Any] = json.loads,
) -> WebAppInitData:
    """
    Validate raw WebApp init data and return it as WebAppInitData object

    Raise :obj:`ValueError` when data is invalid

    :param token: bot token
    :param init_data: data from frontend to be parsed and validated
    :param loads:
    :return:
    """
    if check_webapp_signature(token, init_data):
        return parse_webapp_init_data(init_data, loads=loads)
    raise ValueError("Invalid init data signature")
