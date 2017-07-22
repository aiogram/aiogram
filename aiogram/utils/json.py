try:
    import ujson as json
except ImportError:
    import json


def dumps(data):
    return json.dumps(data)


def loads(data):
    return json.loads(data)
