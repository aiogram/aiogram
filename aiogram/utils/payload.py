from aiogram.utils import json

DEFAULT_FILTER = ['self']


def generate_payload(exclude=None, **kwargs):
    if exclude is None:
        exclude = []
    return {key: value for key, value in kwargs.items() if
            key not in exclude + DEFAULT_FILTER
            and value
            and not key.startswith('_')}


def prepare_arg(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    elif hasattr(value, 'to_json'):
        return json.dumps(value.to_json())
    return value
