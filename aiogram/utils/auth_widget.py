import collections
import hashlib
import hmac


def check_token(data, token):
    """
    Validate auth token
    https://core.telegram.org/widgets/login#checking-authorization

    Source: https://gist.github.com/xen/e4bea72487d34caa28c762776cf655a3

    :param data:
    :param token:
    :return:
    """
    secret = hashlib.sha256()
    secret.update(token.encode('utf-8'))
    sorted_params = collections.OrderedDict(sorted(data.items()))
    param_hash = sorted_params.pop('hash', '') or ''
    msg = "\n".join(["{}={}".format(k, v) for k, v in sorted_params.items()])

    if param_hash == hmac.new(secret.digest(), msg.encode('utf-8'), digestmod=hashlib.sha256).hexdigest():
        return True
    return False
