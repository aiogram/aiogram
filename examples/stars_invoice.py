import asyncio
import logging
from os import getenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery

TOKEN = getenv("BOT_TOKEN")

GOODS = {  # Fake storage for goods, in real life it should be a database
    "demo": 1,
    "another": 0,
}

logger = logging.getLogger(__name__)
invoices_router = Router(name=__name__)


@invoices_router.message(Command("start"))
async def command_start(message: Message) -> None:
    # Send demo invoice to user, the payment will be refunded after successful payment
    await message.answer_invoice(
        title="Demo invoice",
        description="Demo invoice description",
        prices=[
            LabeledPrice(label="Demo", amount=42),
        ],
        payload="demo",
        currency="XTR",
    )


@invoices_router.pre_checkout_query(F.invoice_payload == "demo")
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    # if your product is available for sale,
    # confirm that you are ready to accept payment
    if GOODS.get(query.invoice_payload) > 0:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="The product is out of stock")


@invoices_router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot) -> None:
    await bot.refund_star_payment(
        user_id=message.from_user.id,
        telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
    )
    await message.answer("Thanks. Your payment has been refunded.")


async def main() -> None:
    bot = Bot(token=TOKEN)

    dispatcher = Dispatcher()
    dispatcher.include_router(invoices_router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
