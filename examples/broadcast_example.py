import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


def get_users():
    """
    Return users list

    In this example returns some random ID's
    """
    yield from (61043901, 78238238, 78378343, 98765431, 12345678)


async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender

    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcaster() -> int:
    """
    Simple broadcaster

    :return: Count of messages
    """
    count = 0
    try:
        for user_id in get_users():
            if await send_message(user_id, '<b>Hello!</b>'):
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages successful sent.")

    return count


if __name__ == '__main__':
    # Execute broadcaster
    executor.start(dp, broadcaster())
