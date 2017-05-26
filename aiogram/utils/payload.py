DEFAULT_FILTER = ['self']


def generate_payload(skip_items=None, **kwargs):
    if skip_items is None:
        skip_items = []
    return {key: value for key, value in kwargs.items() if key not in skip_items + DEFAULT_FILTER and value}
