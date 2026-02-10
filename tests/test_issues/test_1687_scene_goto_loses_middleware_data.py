from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from aiogram import BaseMiddleware, Dispatcher
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.fsm.scene import After, Scene, SceneRegistry, on
from aiogram.types import Chat, Message, TelegramObject, Update, User
from tests.mocked_bot import MockedBot


class TestContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["test_context"] = "context from middleware"
        return await handler(event, data)


class TargetScene(Scene, state="target"):
    entered_with_context: str | None = None

    @on.message.enter()
    async def on_enter(self, message: Message, test_context: str) -> None:
        type(self).entered_with_context = test_context


class StartScene(Scene, state="start"):
    @on.message.enter()
    async def on_start(self, message: Message) -> None:
        await self.wizard.goto(TargetScene)


class StartSceneWithAfter(Scene, state="start_with_after"):
    @on.message(after=After.goto(TargetScene))
    async def goto_target_with_after(self, message: Message) -> None:
        pass


async def test_scene_goto_preserves_message_middleware_data(bot: MockedBot) -> None:
    dp = Dispatcher()
    registry = SceneRegistry(dp)
    registry.add(StartScene, TargetScene)
    dp.message.register(StartScene.as_handler(), CommandStart())
    dp.message.middleware(TestContextMiddleware())

    TargetScene.entered_with_context = None

    update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=42, type=ChatType.PRIVATE),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            text="/start",
        ),
    )

    await dp.feed_update(bot, update)

    assert TargetScene.entered_with_context == "context from middleware"


async def test_scene_after_goto_preserves_message_middleware_data(bot: MockedBot) -> None:
    dp = Dispatcher()
    registry = SceneRegistry(dp)
    registry.add(StartSceneWithAfter, TargetScene)
    dp.message.register(StartSceneWithAfter.as_handler(), CommandStart())
    dp.message.middleware(TestContextMiddleware())

    TargetScene.entered_with_context = None

    await dp.feed_update(
        bot,
        Update(
            update_id=1,
            message=Message(
                message_id=1,
                date=datetime.now(),
                chat=Chat(id=42, type=ChatType.PRIVATE),
                from_user=User(id=42, is_bot=False, first_name="Test"),
                text="/start",
            ),
        ),
    )

    await dp.feed_update(
        bot,
        Update(
            update_id=2,
            message=Message(
                message_id=2,
                date=datetime.now(),
                chat=Chat(id=42, type=ChatType.PRIVATE),
                from_user=User(id=42, is_bot=False, first_name="Test"),
                text="go",
            ),
        ),
    )

    assert TargetScene.entered_with_context == "context from middleware"
