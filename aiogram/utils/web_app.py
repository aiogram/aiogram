import hashlib
import hmac
from operator import itemgetter
from typing import Callable, Any, Dict
from urllib.parse import parse_qsl


def check_webapp_signature(token: str, init_data: str) -> bool:
    """
    Check incoming WebApp init data signature

    Source: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

    :param token:
    :param init_data:
    :return:
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        # Init data is not a valid query string
        return False
    if "hash" not in parsed_data:
        # Hash is not present in init data
        return False

    hash_ = parsed_data.pop('hash')
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=token.encode(), digestmod=hashlib.sha256
    )
    calculated_hash = hmac.new(
        key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    return calculated_hash == hash_


def parse_init_data(init_data: str, _loads: Callable[..., Any]) -> Dict[str, Any]:
    """
    Parse WebApp init data and return it as dict

    :param init_data:
    :param _loads:
    :return:
    """
    result = {}
    for key, value in parse_qsl(init_data):
        if (value.startswith('[') and value.endswith(']')) or (value.startswith('{') and value.endswith('}')):
            value = _loads(value)
        result[key] = value
    return result


def safe_parse_webapp_init_data(token: str, init_data: str, _loads: Callable[..., Any]) -> Dict[str, Any]:
    """
    Validate WebApp init data and return it as dict

    :param token:
    :param init_data:
    :param _loads:
    :return:
    """
    if check_webapp_signature(token, init_data):
        return parse_init_data(init_data, _loads)
    raise ValueError("Invalid init data signature")
