"""
Deep linking

Telegram bots have a deep linking mechanism, that allows for passing
additional parameters to the bot on startup. It could be a command that
launches the bot — or an auth token to connect the user's Telegram
account to their account on some external service.

You can read detailed description in the source:
https://core.telegram.org/bots#deep-linking

We have add some utils to get deep links more handy.

Basic link example:

    .. code-block:: python

        from aiogram.utils.deep_linking import get_start_link
        link = await get_start_link('foo')

        # result: 'https://t.me/MyBot?start=foo'

Encoded link example:

    .. code-block:: python

        from aiogram.utils.deep_linking import get_start_link

        link = await get_start_link('foo', encode=True)
        # result: 'https://t.me/MyBot?start=Zm9v'

Decode it back example:
    .. code-block:: python

        from aiogram.utils.deep_linking import decode_payload
        from aiogram.types import Message

        @dp.message_handler(commands=["start"])
        async def handler(message: Message):
            args = message.get_args()
            payload = decode_payload(args)
            await message.answer(f"Your payload: {payload}")

"""
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Literal, cast

from aiogram import Bot
from aiogram.utils.link import create_telegram_link

BAD_PATTERN = re.compile(r"[^_A-z0-9-]")


async def create_start_link(bot: Bot, payload: str, encode: bool = False) -> str:
    """
    Create 'start' deep link with your payload.

    If you need to encode payload or pass special characters -
        set encode as True

    :param bot: bot instance
    :param payload: args passed with /start
    :param encode: encode payload with base64url
    :return: link
    """
    username = (await bot.me()).username
    return create_deep_link(
        username=cast(str, username), link_type="start", payload=payload, encode=encode
    )


async def create_startgroup_link(bot: Bot, payload: str, encode: bool = False) -> str:
    """
    Create 'startgroup' deep link with your payload.

    If you need to encode payload or pass special characters -
        set encode as True

    :param bot: bot instance
    :param payload: args passed with /start
    :param encode: encode payload with base64url
    :return: link
    """
    username = (await bot.me()).username
    return create_deep_link(
        username=cast(str, username), link_type="startgroup", payload=payload, encode=encode
    )


def create_deep_link(
    username: str, link_type: Literal["start", "startgroup"], payload: str, encode: bool = False
) -> str:
    """
    Create deep link.

    :param username:
    :param link_type: `start` or `startgroup`
    :param payload: any string-convertible data
    :param encode: pass True to encode the payload
    :return: deeplink
    """
    if not isinstance(payload, str):
        payload = str(payload)

    if encode:
        payload = encode_payload(payload)

    if re.search(BAD_PATTERN, payload):
        raise ValueError(
            "Wrong payload! Only A-Z, a-z, 0-9, _ and - are allowed. "
            "Pass `encode=True` or encode payload manually."
        )

    if len(payload) > 64:
        raise ValueError("Payload must be up to 64 characters long.")

    return create_telegram_link(username, **{cast(str, link_type): payload})


def encode_payload(payload: str) -> str:
    """Encode payload with URL-safe base64url."""
    payload = str(payload)
    bytes_payload: bytes = urlsafe_b64encode(payload.encode())
    str_payload = bytes_payload.decode()
    return str_payload.replace("=", "")


def decode_payload(payload: str) -> str:
    """Decode payload with URL-safe base64url."""
    payload += "=" * (4 - len(payload) % 4)
    result: bytes = urlsafe_b64decode(payload)
    return result.decode()
