import json

def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=False
    )

def _byteify(data, ignore_dicts=False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=ignore_dicts) for item in data ]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=ignore_dicts): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data
