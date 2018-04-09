LIST_MD_SYMBOLS = '*_`['

MD_SYMBOLS = (
    (LIST_MD_SYMBOLS[0], LIST_MD_SYMBOLS[0]),
    (LIST_MD_SYMBOLS[1], LIST_MD_SYMBOLS[1]),
    (LIST_MD_SYMBOLS[2], LIST_MD_SYMBOLS[2]),
    (LIST_MD_SYMBOLS[2] * 3 + '\n', '\n' + LIST_MD_SYMBOLS[2] * 3),
    ('<b>', '</b>'),
    ('<i>', '</i>'),
    ('<code>', '</code>'),
    ('<pre>', '</pre>'),
)

HTML_QUOTES_MAP = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    '"': '&quot;'
}

_HQS = HTML_QUOTES_MAP.keys()  # HQS for HTML QUOTES SYMBOLS


def _join(*content, sep=' '):
    return sep.join(map(str, content))


def _escape(s, symbols=LIST_MD_SYMBOLS):
    for symbol in symbols:
        s = s.replace(symbol, '\\' + symbol)
    return s


def _md(string, symbols=('', '')):
    start, end = symbols
    return start + string + end


def quote_html(content):
    """
    Quote HTML symbols

    All <, >, & and " symbols that are not a part of a tag or
    an HTML entity must be replaced with the corresponding HTML entities
    (< with &lt; > with &gt; & with &amp and " with &quot).

    :param content: str
    :return: str
    """
    new_content = ''
    for symbol in content:
        new_content += HTML_QUOTES_MAP[symbol] if symbol in _HQS else symbol
    return new_content


def text(*content, sep=' '):
    """
    Join all elements with a separator

    :param content:
    :param sep:
    :return:
    """
    return _join(*content, sep=sep)


def bold(*content, sep=' '):
    """
    Make bold text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[0])


def hbold(*content, sep=' '):
    """
    Make bold text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return _md(quote_html(_join(*content, sep=sep)), symbols=MD_SYMBOLS[4])


def italic(*content, sep=' '):
    """
    Make italic text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[1])


def hitalic(*content, sep=' '):
    """
    Make italic text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return _md(quote_html(_join(*content, sep=sep)), symbols=MD_SYMBOLS[5])


def code(*content, sep=' '):
    """
    Make mono-width text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[2])


def hcode(*content, sep=' '):
    """
    Make mono-width text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return _md(quote_html(_join(*content, sep=sep)), symbols=MD_SYMBOLS[6])


def pre(*content, sep='\n'):
    """
    Make mono-width text block (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return _md(_join(*content, sep=sep), symbols=MD_SYMBOLS[3])


def hpre(*content, sep='\n'):
    """
    Make mono-width text block (HTML)

    :param content:
    :param sep:
    :return:
    """
    return _md(quote_html(_join(*content, sep=sep)), symbols=MD_SYMBOLS[7])


def link(title, url):
    """
    Format URL (Markdown)

    :param title:
    :param url:
    :return:
    """
    return "[{0}]({1})".format(title, url)


def hlink(title, url):
    """
    Format URL (HTML)

    :param title:
    :param url:
    :return:
    """
    return '<a href="{0}">{1}</a>'.format(url, quote_html(title))


def escape_md(*content, sep=' '):
    """
    Escape markdown text

    E.g. for usernames

    :param content:
    :param sep:
    :return:
    """
    return _escape(_join(*content, sep=sep))


def hide_link(url):
    """
    Hide URL (HTML only)
    Can be used for adding an image to a text message

    :param url:
    :return:
    """
    return f'<a href="{url}">&#8203;</a>'
