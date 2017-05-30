DEFAULT_FILTER = ['self']


def generate_payload(exclude=None, **kwargs):
    if exclude is None:
        exclude = []
    return {key: value for key, value in kwargs.items() if
            key not in exclude + DEFAULT_FILTER
            and value
            and not key.startswith('_')}
