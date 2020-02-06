from .text_decorations import html_decoration, markdown_decoration

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


def quote_html(*content, sep=" "):
    """
    Quote HTML symbols

    All <, >, & and " symbols that are not a part of a tag or
    an HTML entity must be replaced with the corresponding HTML entities
    (< with &lt; > with &gt; & with &amp and " with &quot).

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.quote(_join(*content, sep=sep))


def escape_md(*content, sep=" "):
    """
    Escape markdown text

    E.g. for usernames

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.quote(_join(*content, sep=sep))


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
    return markdown_decoration.bold.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def hbold(*content, sep=" "):
    """
    Make bold text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.bold.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def italic(*content, sep=" "):
    """
    Make italic text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.italic.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def hitalic(*content, sep=" "):
    """
    Make italic text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.italic.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def code(*content, sep=" "):
    """
    Make mono-width text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.code.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def hcode(*content, sep=" "):
    """
    Make mono-width text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.code.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def pre(*content, sep="\n"):
    """
    Make mono-width text block (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.pre.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def hpre(*content, sep="\n"):
    """
    Make mono-width text block (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.pre.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def underline(*content, sep=" "):
    """
    Make underlined text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.underline.format(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hunderline(*content, sep=" "):
    """
    Make underlined text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.underline.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def strikethrough(*content, sep=" "):
    """
    Make strikethrough text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.strikethrough.format(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hstrikethrough(*content, sep=" "):
    """
    Make strikethrough text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.strikethrough.format(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def link(title: str, url: str) -> str:
    """
    Format URL (Markdown)

    :param title:
    :param url:
    :return:
    """
    return markdown_decoration.link.format(value=html_decoration.quote(title), link=url)


def hlink(title: str, url: str) -> str:
    """
    Format URL (HTML)

    :param title:
    :param url:
    :return:
    """
    return html_decoration.link.format(value=html_decoration.quote(title), link=url)


def hide_link(url: str) -> str:
    """
    Hide URL (HTML only)
    Can be used for adding an image to a text message

    :param url:
    :return:
    """
    return f'<a href="{url}">&#8203;</a>'
