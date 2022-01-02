from .text_decorations import html_decoration, markdown_decoration

LIST_MD_SYMBOLS = "*_`["

MD_SYMBOLS = (
    (LIST_MD_SYMBOLS[0], LIST_MD_SYMBOLS[0]),
    (LIST_MD_SYMBOLS[1], LIST_MD_SYMBOLS[1]),
    (LIST_MD_SYMBOLS[2], LIST_MD_SYMBOLS[2]),
    (LIST_MD_SYMBOLS[2] * 3 + "\n", "\n" + LIST_MD_SYMBOLS[2] * 3),
    ("||", "||"),
    ("<b>", "</b>"),
    ("<i>", "</i>"),
    ("<code>", "</code>"),
    ("<pre>", "</pre>"),
    ('<span class="tg-spoiler">', "</span>"),
    ("<tg-spoiler>", "</tg-spoiler>"),
)

HTML_QUOTES_MAP = {"<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;"}

_HQS = HTML_QUOTES_MAP.keys()  # HQS for HTML QUOTES SYMBOLS


def quote_html(*content, sep=" ") -> str:
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


def escape_md(*content, sep=" ") -> str:
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


def bold(*content, sep=" ") -> str:
    """
    Make bold text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.bold(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hbold(*content, sep=" ") -> str:
    """
    Make bold text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.bold(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def italic(*content, sep=" ") -> str:
    """
    Make italic text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.italic(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hitalic(*content, sep=" ") -> str:
    """
    Make italic text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.italic(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def spoiler(*content, sep=" ") -> str:
    """
    Make spoiler text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.spoiler(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hspoiler(*content, sep=" ") -> str:
    """
    Make spoiler text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.spoiler(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def code(*content, sep=" ") -> str:
    """
    Make mono-width text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.code(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hcode(*content, sep=" ") -> str:
    """
    Make mono-width text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.code(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def pre(*content, sep="\n") -> str:
    """
    Make mono-width text block (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.pre(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hpre(*content, sep="\n") -> str:
    """
    Make mono-width text block (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.pre(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def underline(*content, sep=" ") -> str:
    """
    Make underlined text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.underline(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hunderline(*content, sep=" ") -> str:
    """
    Make underlined text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.underline(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def strikethrough(*content, sep=" ") -> str:
    """
    Make strikethrough text (Markdown)

    :param content:
    :param sep:
    :return:
    """
    return markdown_decoration.strikethrough(
        value=markdown_decoration.quote(_join(*content, sep=sep))
    )


def hstrikethrough(*content, sep=" ") -> str:
    """
    Make strikethrough text (HTML)

    :param content:
    :param sep:
    :return:
    """
    return html_decoration.strikethrough(
        value=html_decoration.quote(_join(*content, sep=sep))
    )


def link(title: str, url: str) -> str:
    """
    Format URL (Markdown)

    :param title:
    :param url:
    :return:
    """
    return markdown_decoration.link(value=markdown_decoration.quote(title), link=url)


def hlink(title: str, url: str) -> str:
    """
    Format URL (HTML)

    :param title:
    :param url:
    :return:
    """
    return html_decoration.link(value=html_decoration.quote(title), link=url)


def hide_link(url: str) -> str:
    """
    Hide URL (HTML only)
    Can be used for adding an image to a text message

    :param url:
    :return:
    """
    return f'<a href="{url}">&#8288;</a>'
