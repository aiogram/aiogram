try:
    import ujson as json
    IS_UJSON = True
except ImportError:
    import json
    IS_UJSON = False


def dumps(data):
    return json.dumps(data)


def loads(data):
    return json.loads(data)
