"""
Implementation of Telegram site authorization checking mechanism
for more information https://core.telegram.org/widgets/login#checking-authorization

Source: https://gist.github.com/JrooTJunior/887791de7273c9df5277d2b1ecadc839
"""
import collections
import hashlib
import hmac

from aiogram.utils.deprecated import deprecated


@deprecated('`generate_hash` is outdated, please use `check_signature` or `check_integrity`', stacklevel=3)
def generate_hash(data: dict, token: str) -> str:
    """
    Generate secret hash

    :param data:
    :param token:
    :return:
    """
    secret = hashlib.sha256()
    secret.update(token.encode('utf-8'))
    sorted_params = collections.OrderedDict(sorted(data.items()))
    msg = '\n'.join("{}={}".format(k, v) for k, v in sorted_params.items() if k != 'hash')
    return hmac.new(secret.digest(), msg.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()


@deprecated('`check_token` helper was renamed to `check_integrity`', stacklevel=3)
def check_token(data: dict, token: str) -> bool:
    """
    Validate auth token

    :param data:
    :param token:
    :return:
    """
    param_hash = data.get('hash', '') or ''
    return param_hash == generate_hash(data, token)


def check_signature(token: str, hash: str, **kwargs) -> bool:
    """
    Generate hexadecimal representation
    of the HMAC-SHA-256 signature of the data-check-string
    with the SHA256 hash of the bot's token used as a secret key

    :param token:
    :param hash:
    :param kwargs: all params received on auth
    :return:
    """
    secret = hashlib.sha256(token.encode('utf-8'))
    check_string = '\n'.join(map(lambda k: f'{k}={kwargs[k]}', sorted(kwargs)))
    hmac_string = hmac.new(secret.digest(), check_string.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
    return hmac_string == hash


def check_integrity(token: str, data: dict) -> bool:
    """
    Verify the authentication and the integrity
    of the data received on user's auth

    :param token: Bot's token
    :param data: all data that came on auth
    :return:
    """
    return check_signature(token, **data)
