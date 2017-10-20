import json

try:
    import ujson

    _UJSON_IS_AVAILABLE = True
except ImportError:
    _UJSON_IS_AVAILABLE = False

_use_ujson = _UJSON_IS_AVAILABLE


def disable_ujson():
    global _use_ujson
    _use_ujson = False


def dumps(data):
    if _use_ujson:
        return ujson.dumps(data)
    return json.dumps(data)


def loads(data):
    if _use_ujson:
        return ujson.loads(data)
    return json.loads(data)
