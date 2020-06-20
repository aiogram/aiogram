import datetime
import secrets

from babel.support import LazyProxy

from aiogram import types
from . import json

DEFAULT_FILTER = ['self', 'cls']


def generate_payload(exclude=None, **kwargs):
    """
    Generate payload

    Usage: payload = generate_payload(**locals(), exclude=['foo'])

    :param exclude:
    :param kwargs:
    :return: dict
    """
    if exclude is None:
        exclude = []
    return {key: value for key, value in kwargs.items() if
            key not in exclude + DEFAULT_FILTER
            and value is not None
            and not key.startswith('_')}


def _normalize(obj):
    """
    Normalize dicts and lists

    :param obj:
    :return: normalized object
    """
    if isinstance(obj, list):
        return [_normalize(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items() if v is not None}
    elif hasattr(obj, 'to_python'):
        return obj.to_python()
    return obj


def prepare_arg(value):
    """
    Stringify dicts/lists and convert datetime/timedelta to unix-time

    :param value:
    :return:
    """
    if value is None:
        return value
    if isinstance(value, (list, dict)) or hasattr(value, 'to_python'):
        return json.dumps(_normalize(value))
    if isinstance(value, datetime.timedelta):
        now = datetime.datetime.now()
        return int((now + value).timestamp())
    if isinstance(value, datetime.datetime):
        return round(value.timestamp())
    if isinstance(value, LazyProxy):
        return str(value)
    return value


def prepare_file(payload, files, key, file):
    if isinstance(file, str):
        payload[key] = file
    elif file is not None:
        files[key] = file


def prepare_attachment(payload, files, key, file):
    if isinstance(file, str):
        payload[key] = file
    elif isinstance(file, types.InputFile):
        payload[key] = file.attach
        files[file.attachment_key] = file.file
    elif file is not None:
        file_attach_name = secrets.token_urlsafe(16)
        payload[key] = "attach://" + file_attach_name
        files[file_attach_name] = file
