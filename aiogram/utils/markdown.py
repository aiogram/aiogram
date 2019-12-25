from .text_decorations import html, markdown

LIST_MD_SYMBOLS = "*_`["

MD_SYMBOLS = (
    (LIST_MD_SYMBOLS[0], LIST_MD_SYMBOLS[0]),
    (LIST_MD_SYMBOLS[1], LIST_MD_SYMBOLS[1]),
    (LIST_MD_SYMBOLS[2], LIST_MD_SYMBOLS[2]),
    (LIST_MD_SYMBOLS[2] * 3 + "\n", "\n" + LIST_MD_SYMBOLS[2] * 3),
    ("<b>", "</b>"),
    ("<i>", "</i>"),
    ("<code>", "</code>"),
    ("<pre>", "</pre>"),
)

HTML_QUOTES_MAP = {"<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;"}

_HQS = HTML_QUOTES_MAP.keys()  # HQS for HTML QUOTES SYMBOLS


def _join(*content, sep=" "):
    return sep.join(map(str, content))


def text(*content, sep=" "):
    """
    Join all elements with a separator

    :param content:
    :param sep:
    :return:
    """
    return _join(*content, sep=sep)


def bold(*content, sep=" "):
    """
    Make bold text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown.bold.format(value=html.quote(_join(*content, sep=sep)))


def hbold(*content, sep=" "):
    """
    Make bold text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html.bold.format(value=html.quote(_join(*content, sep=sep)))


def italic(*content, sep=" "):
    """
    Make italic text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown.italic.format(value=html.quote(_join(*content, sep=sep)))


def hitalic(*content, sep=" "):
    """
    Make italic text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html.italic.format(value=html.quote(_join(*content, sep=sep)))


def code(*content, sep=" "):
    """
    Make mono-width text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown.code.format(value=html.quote(_join(*content, sep=sep)))


def hcode(*content, sep=" "):
    """
    Make mono-width text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html.code.format(value=html.quote(_join(*content, sep=sep)))


def pre(*content, sep="\n"):
    """
    Make mono-width text block (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown.pre.format(value=html.quote(_join(*content, sep=sep)))


def hpre(*content, sep="\n"):
    """
    Make mono-width text block (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html.pre.format(value=html.quote(_join(*content, sep=sep)))


def underline(*content, sep=" "):
    """
    Make underlined text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown.underline.format(value=markdown.quote(_join(*content, sep=sep)))


def hunderline(*content, sep=" "):
    """
    Make underlined text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html.underline.format(value=html.quote(_join(*content, sep=sep)))


def strikethrough(*content, sep=" "):
    """
    Make strikethrough text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown.strikethrough.format(value=markdown.quote(_join(*content, sep=sep)))


def hstrikethrough(*content, sep=" "):
    """
    Make strikethrough text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html.strikethrough.format(value=html.quote(_join(*content, sep=sep)))


def link(title: str, url: str) -> str:
    """
    Format URL (Markdown)

    :param title:
    :param url:
    :return:
    """
    return markdown.link.format(value=html.quote(title), link=url)


def hlink(title: str, url: str) -> str:
    """
    Format URL (HTML)

    :param title:
    :param url:
    :return:
    """
    return html.link.format(value=html.quote(title), link=url)


def hide_link(url: str) -> str:
    """
    Hide URL (HTML only)
    Can be used for adding an image to a text message

    :param url:
    :return:
    """
    return f'<a href="{url}">&#8203;</a>'
