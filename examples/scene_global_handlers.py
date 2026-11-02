import asyncio
from os import environ

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.scene import Scene, SceneRegistry, ScenesManager, on
from aiogram.types import Message


class EchoScene(Scene, state="echo"):
    @on.message.enter()
    async def on_enter(self, message: Message) -> None:
        await message.answer("Scene started. Send a message, /help, or /cancel.")

    @on.message()
    async def echo(self, message: Message) -> None:
        await message.answer(f"Scene received: {message.text}")


async def help_command(message: Message) -> None:
    await message.answer("Use /start to enter the scene and /cancel to leave it.")


async def cancel_command(message: Message, scenes: ScenesManager) -> None:
    await scenes.close()
    await message.answer("Cancelled.")


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    global_router = Router(name="global_commands")
    global_router.message.register(help_command, Command("help"))
    global_router.message.register(cancel_command, Command("cancel"))

    # Include global commands before the Scene's catch-all message handler.
    dispatcher.include_router(global_router)
    dispatcher.message.register(EchoScene.as_handler(), CommandStart())
    registry = SceneRegistry(dispatcher)
    registry.add(EchoScene)
    return dispatcher


async def main() -> None:
    dispatcher = create_dispatcher()
    bot = Bot(token=environ["BOT_TOKEN"])
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
