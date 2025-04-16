from datetime import datetime
from typing import Any, Awaitable, Callable, Dict
from unittest.mock import AsyncMock

import pytest

from aiogram import BaseMiddleware, Dispatcher, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.scene import Scene, SceneRegistry, ScenesManager, on
from aiogram.types import Chat, Message, TelegramObject, Update, User
from tests.mocked_bot import MockedBot


class EchoScene(Scene, state="test"):
    @on.message.enter()
    async def greetings(self, message: Message, test_context: str):
        await message.answer(f"Echo mode enabled. Context: {test_context}.")

    @on.message(F.text)
    async def echo(self, message: Message, test_context: str):
        await message.reply(f"Your input: {message.text} and Context: {test_context}.")


class TestMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["test_context"] = "Custom context here"
        return await handler(event, data)


@pytest.mark.asyncio
async def test_middleware_data_passed_to_scene(bot: MockedBot):
    """Test that middleware data is correctly passed to the scene when using as_handler()."""
    # Create a dispatcher
    dp = Dispatcher()

    # Register the scene handler with the command filter
    dp.message.register(EchoScene.as_handler(), Command("test"))

    # Register the scene with the registry
    scene_registry = SceneRegistry(dp)
    scene_registry.add(EchoScene)

    # Register the middleware
    dp.message.outer_middleware.register(TestMiddleware())

    # Create a proper message with the command
    chat = Chat(id=123, type=ChatType.PRIVATE)
    user = User(id=456, is_bot=False, first_name="Test User")
    message = Message(message_id=1, date=datetime.now(), from_user=user, chat=chat, text="/test")
    update = Update(message=message, update_id=1)

    # Mock the ScenesManager.enter method
    original_enter = ScenesManager.enter
    ScenesManager.enter = AsyncMock()

    try:
        # Process the update
        await dp.feed_update(bot, update)

        # Verify that ScenesManager.enter was called with the test_context from middleware
        ScenesManager.enter.assert_called_once()
        args, kwargs = ScenesManager.enter.call_args
        assert "test_context" in kwargs
        assert kwargs["test_context"] == "Custom context here"
    finally:
        # Restore the original method
        ScenesManager.enter = original_enter
