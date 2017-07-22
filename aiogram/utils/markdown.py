LIST_MD_SYMBOLS = '*_`['

MD_SYMBOLS = (
    (LIST_MD_SYMBOLS[0], LIST_MD_SYMBOLS[0]),
    (LIST_MD_SYMBOLS[1], LIST_MD_SYMBOLS[1]),
    (LIST_MD_SYMBOLS[2], LIST_MD_SYMBOLS[2]),
    (LIST_MD_SYMBOLS[2] * 3 + '\n', '\n' + LIST_MD_SYMBOLS[2] * 3)
)


def _join(*content, sep=' '):
    return sep.join(map(str, content))


def _escape(s, symbols=LIST_MD_SYMBOLS):
    for symbol in symbols:
        s = s.replace(symbol, '\\' + symbol)
    return s


def _md(string, symbols=('', '')):
    start, end = symbols
    return start + string + end


def text(*content, sep=' '):
    return _md('', _join(*content, sep=sep))


def bold(*content, sep=' '):
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[0])


def italic(*content, sep=' '):
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[1])


def code(*content, sep=' '):
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[2])


def pre(*content, sep='\n'):
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[3])


def link(title, url):
    return f"[{_escape(title)}]({url})"


def escape_md(*content, sep=' '):
    return _escape(_join(*content, sep=sep))
