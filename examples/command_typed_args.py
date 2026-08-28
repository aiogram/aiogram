import asyncio
import logging
import random
import sys
from os import getenv

from pydantic import BaseModel

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart, DeeplinkCommand, or_f
from aiogram.filters.command import DeeplinkData, NamedCodec, PositionalCodec
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link

TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()


class RollArgs(BaseModel):
    sides: int = 6
    count: int = 1


@dp.message(Command("roll", data=RollArgs, codec=PositionalCodec(sep=" ")))
async def cmd_roll(message: Message, command: CommandObject[RollArgs]) -> None:
    """Roll dice. Usage: /roll [sides] [count]"""
    results = [random.randint(1, command.parsed.sides) for _ in range(command.parsed.count)]
    await message.answer(f"🎲 {results} (sum: {sum(results)})")


class RemindArgs(BaseModel):
    text: str = ""
    delay: int = 5


@dp.message(Command("remind", data=RemindArgs, codec=NamedCodec()))
async def cmd_remind(message: Message, command: CommandObject[RemindArgs]) -> None:
    """Set a reminder. Usage: /remind text=Buy_milk delay=10"""
    await message.answer(f"⏰ Remind '{command.parsed.text}' in {command.parsed.delay} min.")


class InvitePayload(DeeplinkData, prefix="inv", encoded=True):
    """Encoded deeplink payload. Example payload: ``invNDJfYWRtaW4``"""

    group_id: int
    role: str = "member"


@dp.message(DeeplinkCommand(data=InvitePayload))
async def deeplink_invite(message: Message, command: CommandObject[InvitePayload]) -> None:
    """Handles /start with an encoded invite payload."""
    await message.answer(
        f"👋 Welcome to group #{command.parsed.group_id} as {command.parsed.role}!"
    )


class OrderPayload(DeeplinkData, prefix="order"):
    """Plain deeplink payload. Example payload: ``order99_SALE``"""

    order_id: int
    promo: str | None = None


@dp.message(DeeplinkCommand(data=OrderPayload))
async def deeplink_order(message: Message, command: CommandObject[OrderPayload]) -> None:
    """Handles /start with a plain order payload."""
    await message.answer(
        f"🛒 Order #{command.parsed.order_id}, promo: {command.parsed.promo or '—'}"
    )


class PromoData(DeeplinkData, prefix="deal"):
    """Combined payload for /promo and /start deeplink. Example: ``dealSALE_50``"""

    code: str = ""
    discount: int = 0


@dp.message(
    or_f(
        Command("promo", data=PromoData, codec=PositionalCodec(sep=" ")),
        DeeplinkCommand(data=PromoData),
    )
)
async def cmd_promo(message: Message, command: CommandObject[PromoData]) -> None:
    """Apply a promo code. Via command: /promo SALE 50  |  Via deeplink: /start dealSALE_50"""
    await message.answer(f"🏷 Promo {command.parsed.code}: {command.parsed.discount}% off!")


class BanArgs(BaseModel):
    user_id: int
    reason: str


@dp.message(Command("ban", data=BanArgs, codec=PositionalCodec(sep=" ")))
async def cmd_ban(message: Message, command: CommandObject[BanArgs]) -> None:
    """Ban a user. Usage: /ban <user_id> <reason>"""
    await message.answer(f"🔨 Banned {command.parsed.user_id}: {command.parsed.reason}")


@dp.message(Command("ban"))
async def cmd_ban_usage(message: Message) -> None:
    """Fallback when /ban is sent without required arguments."""
    await message.answer("Usage: /ban <user_id> <reason>")


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Hello! This bot demonstrates typed command arguments.\n\n"
        "<b>Positional args</b>\n"
        "/roll &lt;sides&gt; &lt;count&gt; — roll dice\n\n"
        "<b>Named args</b>\n"
        "/remind text=Buy_milk delay=10\n\n"
        "<b>Required args (fallback on missing)</b>\n"
        "/ban &lt;user_id&gt; &lt;reason&gt;\n\n"
        "<b>Deeplinks</b>\n"
        "/genlinks — get clickable /start links\n\n"
        "<b>Combined (command + deeplink)</b>\n"
        "/promo CODE DISCOUNT"
    )


@dp.message(Command("genlinks"))
async def cmd_genlinks(message: Message, bot: Bot) -> None:
    invite_link = await create_start_link(bot, InvitePayload(group_id=42, role="admin").pack())
    order_link = await create_start_link(bot, OrderPayload(order_id=99, promo="SALE").pack())
    promo_link = await create_start_link(bot, PromoData(code="SALE", discount=50).pack())

    await message.answer(
        f"Invite (encoded):\n{invite_link}\n\n"
        f"Order (plain):\n{order_link}\n\n"
        f"Promo (combined):\n{promo_link}"
    )


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
