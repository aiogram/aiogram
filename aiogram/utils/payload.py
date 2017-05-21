DEFAULT_FILTER = ['self']


def generate_payload(skip_items=DEFAULT_FILTER, **kwargs):
    return {key: value for key, value in kwargs.items() if key not in skip_items and value}
