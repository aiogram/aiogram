"""
Deep linking

Telegram bots have a deep linking mechanism, that allows for passing additional
parameters to the bot on startup. It could be a command that launches the bot — or
an auth token to connect the user's Telegram account to their account on some
external service.

You can read detailed description in the source:
https://core.telegram.org/bots#deep-linking

We have add some utils to get deep links more handy.

Basic link example:

    .. code-block:: python

        from aiogram.utils.deep_linking import get_start_link
        link = await get_start_link('foo')  # result: 'https://t.me/MyBot?start=foo'

Encoded link example:

    .. code-block:: python

        from aiogram.utils.deep_linking import get_start_link, decode_payload
        link = await get_start_link('foo', encode=True)  # result: 'https://t.me/MyBot?start=Zm9v'
        # and decode it back:
        payload = decode_payload('Zm9v')  # result: 'foo'

"""


async def get_start_link(payload: str, encode=False) -> str:
    """
    Use this method to handy get 'start' deep link with your payload.
    If you need to encode payload or pass special characters - set encode as True

    :param payload: args passed with /start
    :param encode: encode payload with base64url
    :return: link
    """
    return await _create_link('start', payload, encode)


async def get_startgroup_link(payload: str, encode=False) -> str:
    """
    Use this method to handy get 'startgroup' deep link with your payload.
    If you need to encode payload or pass special characters - set encode as True

    :param payload: args passed with /start
    :param encode: encode payload with base64url
    :return: link
    """
    return await _create_link('startgroup', payload, encode)


async def _create_link(link_type, payload: str, encode=False):
    bot = await _get_bot_user()
    payload = filter_payload(payload)
    if encode:
        payload = encode_payload(payload)
    return f'https://t.me/{bot.username}?{link_type}={payload}'


def encode_payload(payload: str) -> str:
    """ Encode payload with URL-safe base64url. """
    from base64 import urlsafe_b64encode
    result: bytes = urlsafe_b64encode(payload.encode())
    return result.decode()


def decode_payload(payload: str) -> str:
    """ Decode payload with URL-safe base64url. """
    from base64 import urlsafe_b64decode
    result: bytes = urlsafe_b64decode(payload + '=' * (4 - len(payload) % 4))
    return result.decode()


def filter_payload(payload: str) -> str:
    """ Convert payload to text and search for not allowed symbols. """
    import re

    # convert to string
    if not isinstance(payload, str):
        payload = str(payload)

    # search for not allowed characters
    if re.search(r'[^_A-z0-9-]', payload):
        message = ('Wrong payload! Only A-Z, a-z, 0-9, _ and - are allowed. '
                   'We recommend to encode parameters with binary and other '
                   'types of content.')
        raise ValueError(message)

    return payload


async def _get_bot_user():
    """ Get current user of bot. """
    from ..bot import Bot
    bot = Bot.get_current()
    return await bot.me
