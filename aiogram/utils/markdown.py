MD_SYMBOLS = '*_`'


def _rst(symbol, *content, sep=' '):
    start, end = (symbol, symbol) if isinstance(symbol, str) else (symbol[0], symbol[1])
    return start + sep.join(map(str, content)) + end


def text(*content, sep=' '):
    return _rst('', *content, sep=sep)


def bold(*content, sep=' '):
    return _rst(MD_SYMBOLS[0], *content, sep=sep)


def italic(*content, sep=' '):
    return _rst(MD_SYMBOLS[1], *content, sep=sep)


def code(*content, sep=' '):
    return _rst(MD_SYMBOLS[2], *content, sep=sep)


def pre(*content, sep='\n'):
    return _rst(('```\n', '\n```'), *content, sep=sep)


def link(title, url):
    return f"[{title}]({url})"


def escape_md(*content, sep=' '):
    result = text(*content, sep=sep)
    for symbol in MD_SYMBOLS + '[':
        result = result.replace(symbol, '\\' + symbol)
    return result
