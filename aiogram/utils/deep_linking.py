"""
Deep linking

Telegram bots have a deep linking mechanism, that allows for passing
additional parameters to the bot on startup. It could be a command that
launches the bot — or an auth token to connect the user's Telegram
account to their account on some external service.

You can read detailed description in the source:
https://core.telegram.org/bots#deep-linking

We have added some utils to get deep links more handy.

Basic link example:

    .. code-block:: python

        from aiogram.utils.deep_linking import create_start_link

        link = await create_start_link(bot, 'foo')

        # result: 'https://t.me/MyBot?start=foo'

Encoded link example:

    .. code-block:: python

        from aiogram.utils.deep_linking import create_start_link

        link = await create_start_link(bot, 'foo', encode=True)
        # result: 'https://t.me/MyBot?start=Zm9v'

Decode it back example:
    .. code-block:: python

        from aiogram.utils.deep_linking import decode_payload
        from aiogram.filters import CommandStart, CommandObject
        from aiogram.types import Message

        @router.message(CommandStart(deep_link=True))
        async def handler(message: Message, command: CommandObject):
            args = command.args
            payload = decode_payload(args)
            await message.answer(f"Your payload: {payload}")

"""
from __future__ import annotations

__all__ = [
    "create_start_link",
    "create_startgroup_link",
    "create_deep_link",
    "create_telegram_link",
    "encode_payload",
    "decode_payload",
]

import re
from typing import TYPE_CHECKING, Callable, Literal, Optional, cast

from aiogram.utils.link import create_telegram_link
from aiogram.utils.payload import decode_payload, encode_payload

if TYPE_CHECKING:
    from aiogram import Bot

BAD_PATTERN = re.compile(r"[^A-z0-9-]")


async def create_start_link(
    bot: Bot,
    payload: str,
    encode: bool = False,
    encoder: Optional[Callable[[bytes], bytes]] = None,
) -> str:
    """
    Create 'start' deep link with your payload.

    If you need to encode payload or pass special characters -
        set encode as True

    :param bot: bot instance
    :param payload: args passed with /start
    :param encode: encode payload with base64url or custom encoder
    :param encoder: custom encoder callable
    :return: link
    """
    username = (await bot.me()).username
    return create_deep_link(
        username=cast(str, username),
        link_type="start",
        payload=payload,
        encode=encode,
        encoder=encoder,
    )


async def create_startgroup_link(
    bot: Bot,
    payload: str,
    encode: bool = False,
    encoder: Optional[Callable[[bytes], bytes]] = None,
) -> str:
    """
    Create 'startgroup' deep link with your payload.

    If you need to encode payload or pass special characters -
        set encode as True

    :param bot: bot instance
    :param payload: args passed with /start
    :param encode: encode payload with base64url or custom encoder
    :param encoder: custom encoder callable
    :return: link
    """
    username = (await bot.me()).username
    return create_deep_link(
        username=cast(str, username),
        link_type="startgroup",
        payload=payload,
        encode=encode,
        encoder=encoder,
    )


def create_deep_link(
    username: str,
    link_type: Literal["start", "startgroup"],
    payload: str,
    encode: bool = False,
    encoder: Optional[Callable[[bytes], bytes]] = None,
) -> str:
    """
    Create deep link.

    :param username:
    :param link_type: `start` or `startgroup`
    :param payload: any string-convertible data
    :param encode: encode payload with base64url or custom encoder
    :param encoder: custom encoder callable
    :return: deeplink
    """
    if not isinstance(payload, str):
        payload = str(payload)

    if encode or encoder:
        payload = encode_payload(payload, encoder=encoder)

    if re.search(BAD_PATTERN, payload):
        raise ValueError(
            "Wrong payload! Only A-Z, a-z, 0-9, _ and - are allowed. "
            "Pass `encode=True` or encode payload manually."
        )

    if len(payload) > 64:
        raise ValueError("Payload must be up to 64 characters long.")

    return create_telegram_link(username, **{cast(str, link_type): payload})
