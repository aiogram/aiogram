import os

JSON = 'json'
RAPIDJSON = 'rapidjson'
UJSON = 'ujson'

try:
    if 'DISABLE_UJSON' not in os.environ:
        import ujson as json

        mode = UJSON


        def dumps(data):
            return json.dumps(data, ensure_ascii=False)

    else:
        mode = JSON
except ImportError:
    mode = JSON

try:
    if 'DISABLE_RAPIDJSON' not in os.environ:
        import rapidjson as json

        mode = RAPIDJSON


        def dumps(data):
            return json.dumps(data, ensure_ascii=False, number_mode=json.NM_NATIVE,
                              datetime_mode=json.DM_ISO8601 | json.DM_NAIVE_IS_UTC)


        def loads(data):
            return json.loads(data, number_mode=json.NM_NATIVE,
                              datetime_mode=json.DM_ISO8601 | json.DM_NAIVE_IS_UTC)

    else:
        mode = JSON
except ImportError:
    mode = JSON

if mode == JSON:
    import json


    def dumps(data):
        return json.dumps(data, ensure_ascii=False)


    def loads(data):
        return json.loads(data)
