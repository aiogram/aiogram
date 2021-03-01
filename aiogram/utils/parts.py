import typing

MAX_MESSAGE_LENGTH = 4096


def split_text(text: str, length: int = MAX_MESSAGE_LENGTH) -> typing.List[str]:
    """
    Split long text

    :param text:
    :param length:
    :return: list of parts
    :rtype: :obj:`typing.List[str]`
    """
    return [text[i:i + length] for i in range(0, len(text), length)]


def safe_split_text(text: str, length: int = MAX_MESSAGE_LENGTH, split_separator: str = ' ') -> typing.List[str]:
    """
    Split long text

    :param text:
    :param length:
    :param split_separator
    :return:
    """
    # TODO: More informative description

    temp_text = text
    parts = []
    while temp_text:
        if len(temp_text) > length:
            try:
                split_pos = temp_text[:length].rindex(split_separator)
            except ValueError:
                split_pos = length
            if split_pos < length // 4 * 3:
                split_pos = length
            parts.append(temp_text[:split_pos])
            temp_text = temp_text[split_pos:].lstrip()
        else:
            parts.append(temp_text)
            break
    return parts


def paginate(data: typing.Iterable, page: int = 0, limit: int = 10) -> typing.Iterable:
    """
    Slice data over pages

    :param data: any iterable object
    :type data: :obj:`typing.Iterable`
    :param page: number of page
    :type page: :obj:`int`
    :param limit: items per page
    :type limit: :obj:`int`
    :return: sliced object
    :rtype: :obj:`typing.Iterable`
    """
    return data[page * limit:page * limit + limit]
