import warnings

try:
    import emoji
except ImportError:
    raise ImportError('Need install "emoji" module.')


def emojize(text):
    warnings.warn(message="'aiogram.utils.emoji' module deprecated, use emoji symbols directly instead,"
                          "this function will be removed in aiogram v2.22",
                  category=DeprecationWarning, stacklevel=2)
    return emoji.emojize(text, use_aliases=True)


def demojize(text):
    warnings.warn(message="'aiogram.utils.emoji' module deprecated, use emoji symbols directly instead,"
                          "this function will be removed in aiogram v2.22",
                  category=DeprecationWarning, stacklevel=2)
    return emoji.demojize(text)
