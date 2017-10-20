import datetime

from . import json

DEFAULT_FILTER = ['self']


def generate_payload(exclude=None, **kwargs):
    if exclude is None:
        exclude = []
    return {key: value for key, value in kwargs.items() if
            key not in exclude + DEFAULT_FILTER
            and value
            and not key.startswith('_')}


def prepare_arg(value):
    if value is None:
        return value
    elif isinstance(value, (list, dict)):
        return json.dumps(value)
    elif hasattr(value, 'to_python'):
        return json.dumps(value.to_python())
    elif isinstance(value, datetime.timedelta):
        now = datetime.datetime.now()
        return int((now + value).timestamp())
    elif isinstance(value, datetime.datetime):
        return int(value.timestamp())
    return value
