import importlib
import os

JSON = 'json'
RAPIDJSON = 'rapidjson'
UJSON = 'ujson'

# Detect mode
mode = JSON
for json_lib in (RAPIDJSON, UJSON):
    if 'DISABLE_' + json_lib.upper() in os.environ:
        continue

    try:
        json = importlib.import_module(json_lib)
    except ImportError:
        continue
    else:
        mode = json_lib
        break

if mode == RAPIDJSON:

    def dump(*args, **kwargs):
        return json.dump(*args, **kwargs)

    def load(*args, **kwargs):
        return json.load(*args, **kwargs)

    def dumps(data):
        return json.dumps(data, ensure_ascii=False)

    def loads(data):
        return json.loads(data, number_mode=json.NM_NATIVE)


elif mode == UJSON:

    def dump(*args, **kwargs):
        return json.dump(*args, **kwargs)

    def load(*args, **kwargs):
        return json.load(*args, **kwargs)

    def loads(data):
        return json.loads(data)

    def dumps(data):
        return json.dumps(data, ensure_ascii=False)


else:
    import json

    def dump(*args, **kwargs):
        return json.dump(*args, **kwargs)

    def load(*args, **kwargs):
        return json.load(*args, **kwargs)

    def dumps(data):
        return json.dumps(data, ensure_ascii=False)

    def loads(data):
        return json.loads(data)
