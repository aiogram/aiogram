"""
Implementation of Telegram site authorization checking mechanism
for more information https://core.telegram.org/widgets/login#checking-authorization

Source: https://gist.github.com/JrooTJunior/887791de7273c9df5277d2b1ecadc839
"""
import hashlib
import hmac

import collections


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
    msg = '\n'.join(["{}={}".format(k, v) for k, v in sorted_params.items() if k != 'hash'])
    return hmac.new(secret.digest(), msg.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()


def check_token(data: dict, token: str) -> bool:
    """
    Validate auth token

    :param data:
    :param token:
    :return:
    """
    param_hash = data.get('hash', '') or ''
    return param_hash == generate_hash(data, token)
