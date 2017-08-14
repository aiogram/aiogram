from .deprecated import warn_deprecated

try:
    import emoji

    warn_deprecated('Use emoji module instead that util')
except ImportError:
    raise ImportError('Need install "emoji" module.')


def emojize(text):
    return emoji.emojize(text, use_aliases=True)


def demojize(text):
    return emoji.demojize(text)
