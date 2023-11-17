import inspect
import platform
from datetime import datetime
from unittest.mock import ANY, AsyncMock, patch

import pytest

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import (
    ActionContainer,
    After,
    ObserverDecorator,
    ObserverMarker,
    Scene,
    SceneAction,
    SceneHandlerWrapper,
    ScenesManager,
    SceneWizard,
    _empty_handler,
    on,
)
from aiogram.types import Chat, Message, TelegramObject, Update


class TestOnMarker:
    @pytest.mark.parametrize(
        "marker_name",
        [
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "inline_query",
            "chosen_inline_result",
            "callback_query",
            "shipping_query",
            "pre_checkout_query",
            "poll",
            "poll_answer",
            "my_chat_member",
            "chat_member",
            "chat_join_request",
        ],
    )
    def test_marker_name(self, marker_name: str):
        attr = getattr(on, marker_name)
        assert isinstance(attr, ObserverMarker)
        assert attr.name == marker_name


async def test_empty_handler():
    result = await _empty_handler()
    assert result is None


class TestAfter:
    def test_exit(self):
        after = After.exit()
        assert after is not None
        assert after.action == SceneAction.exit
        assert after.scene is None

    def test_back(self):
        after = After.back()
        assert after is not None
        assert after.action == SceneAction.back
        assert after.scene is None

    def test_goto(self):
        after = After.goto("test")
        assert after is not None
        assert after.action == SceneAction.enter
        assert after.scene == "test"


class TestObserverMarker:
    def test_decorator(self):
        marker = ObserverMarker("test")
        decorator = marker(F.test, after=After.back())
        assert isinstance(decorator, ObserverDecorator)
        assert decorator.name == "test"
        assert len(decorator.filters) == 1
        assert decorator.action is None
        assert decorator.after is not None

    def test_enter(self):
        marker = ObserverMarker("test")
        decorator = marker.enter(F.test)
        assert isinstance(decorator, ObserverDecorator)
        assert decorator.name == "test"
        assert len(decorator.filters) == 1
        assert decorator.action == SceneAction.enter
        assert decorator.after is None

    def test_leave(self):
        marker = ObserverMarker("test")
        decorator = marker.leave()
        assert isinstance(decorator, ObserverDecorator)
        assert decorator.name == "test"
        assert len(decorator.filters) == 0
        assert decorator.action == SceneAction.leave
        assert decorator.after is None

    def test_exit(self):
        marker = ObserverMarker("test")
        decorator = marker.exit()
        assert isinstance(decorator, ObserverDecorator)
        assert decorator.name == "test"
        assert len(decorator.filters) == 0
        assert decorator.action == SceneAction.exit
        assert decorator.after is None

    def test_back(self):
        marker = ObserverMarker("test")
        decorator = marker.back()
        assert isinstance(decorator, ObserverDecorator)
        assert decorator.name == "test"
        assert len(decorator.filters) == 0
        assert decorator.action == SceneAction.back
        assert decorator.after is None


class TestObserverDecorator:
    def test_wrap_something(self):
        decorator = ObserverDecorator("test", F.test)

        with pytest.raises(TypeError):
            decorator("test")

    def test_wrap_handler(self):
        decorator = ObserverDecorator("test", F.test)

        def handler():
            pass

        wrapped = decorator(handler)

        assert wrapped is not None
        assert hasattr(wrapped, "__aiogram_handler__")
        assert isinstance(wrapped.__aiogram_handler__, list)
        assert len(wrapped.__aiogram_handler__) == 1

        wrapped2 = decorator(handler)

        assert len(wrapped2.__aiogram_handler__) == 2

    def test_wrap_action(self):
        decorator = ObserverDecorator("test", F.test, action=SceneAction.enter)

        def handler():
            pass

        wrapped = decorator(handler)
        assert wrapped is not None
        assert not hasattr(wrapped, "__aiogram_handler__")
        assert hasattr(wrapped, "__aiogram_action__")

        assert isinstance(wrapped.__aiogram_action__, dict)
        assert len(wrapped.__aiogram_action__) == 1
        assert SceneAction.enter in wrapped.__aiogram_action__
        assert "test" in wrapped.__aiogram_action__[SceneAction.enter]

    def test_observer_decorator_leave(self):
        observer_decorator = ObserverDecorator("Test Name", (F.text,))
        action_container = observer_decorator.leave()
        assert isinstance(action_container, ActionContainer)
        assert action_container.name == "Test Name"
        assert action_container.filters == (F.text,)
        assert action_container.action == SceneAction.leave

    def test_observer_decorator_enter(self):
        observer_decorator = ObserverDecorator("test", (F.text,))
        target = "mock_target"
        action_container = observer_decorator.enter(target)
        assert isinstance(action_container, ActionContainer)
        assert action_container.name == "test"
        assert action_container.filters == (F.text,)
        assert action_container.action == SceneAction.enter
        assert action_container.target == target

    def test_observer_decorator_exit(self):
        observer_decorator = ObserverDecorator("test", (F.text,))
        action_container = observer_decorator.exit()
        assert isinstance(action_container, ActionContainer)
        assert action_container.name == "test"
        assert action_container.filters == (F.text,)
        assert action_container.action == SceneAction.exit

    def test_observer_decorator_back(self):
        observer_decorator = ObserverDecorator("test", (F.text,))
        action_container = observer_decorator.back()
        assert isinstance(action_container, ActionContainer)
        assert action_container.name == "test"
        assert action_container.filters == (F.text,)
        assert action_container.action == SceneAction.back


class TestActionContainer:
    async def test_action_container_execute_enter(self):
        wizard_mock = AsyncMock(spec=SceneWizard)

        action_container = ActionContainer(
            "Test Name", (F.text,), SceneAction.enter, "Test Target"
        )
        await action_container.execute(wizard_mock)

        wizard_mock.goto.assert_called_once_with("Test Target")

    async def test_action_container_execute_leave(self):
        wizard_mock = AsyncMock(spec=SceneWizard)

        action_container = ActionContainer("Test Name", (F.text,), SceneAction.leave)
        await action_container.execute(wizard_mock)

        wizard_mock.leave.assert_called_once()

    async def test_action_container_execute_exit(self):
        wizard_mock = AsyncMock(spec=SceneWizard)

        action_container = ActionContainer("Test Name", (F.text,), SceneAction.exit)
        await action_container.execute(wizard_mock)

        wizard_mock.exit.assert_called_once()

    async def test_action_container_execute_back(self):
        wizard_mock = AsyncMock(spec=SceneWizard)

        action_container = ActionContainer("Test Name", (F.text,), SceneAction.back)
        await action_container.execute(wizard_mock)

        wizard_mock.back.assert_called_once()


class TestSceneHandlerWrapper:
    # @pytest.mark.skipif("PyPy" in platform.python_implementation(), reason="Test skipped on PyPy.")
    async def test_scene_handler_wrapper_call(self):
        class MyScene(Scene):
            pass

        # Mock objects
        handler_mock = AsyncMock(return_value=42)
        state_mock = AsyncMock(spec=FSMContext)
        scenes_mock = AsyncMock(spec=ScenesManager)
        event_update_mock = Update(
            update_id=42,
            message=Message(
                message_id=42,
                text="test",
                date=datetime.now(),
                chat=Chat(
                    type="private",
                    id=42,
                ),
            ),
        )
        kwargs = {"state": state_mock, "scenes": scenes_mock, "event_update": event_update_mock}

        scene_handler_wrapper = SceneHandlerWrapper(MyScene, handler_mock)
        result = await scene_handler_wrapper(event_update_mock, **kwargs)

        # Check whether handler is called with correct arguments
        handler_mock.assert_called_once_with(ANY, event_update_mock, **kwargs)

        # Check whether result is correct
        assert result == 42

    # @pytest.mark.skipif("PyPy" in platform.python_implementation(), reason="Test skipped on PyPy.")
    async def test_scene_handler_wrapper_call_with_after(self):
        class MyScene(Scene):
            pass

        # Mock objects
        handler_mock = AsyncMock(return_value=42)
        state_mock = AsyncMock(spec=FSMContext)
        scenes_mock = AsyncMock(spec=ScenesManager)
        event_update_mock = Update(
            update_id=42,
            message=Message(
                message_id=42,
                text="test",
                date=datetime.now(),
                chat=Chat(
                    type="private",
                    id=42,
                ),
            ),
        )
        kwargs = {"state": state_mock, "scenes": scenes_mock, "event_update": event_update_mock}

        scene_handler_wrapper = SceneHandlerWrapper(MyScene, handler_mock, after=After.exit())

        with patch(
            "aiogram.fsm.scene.ActionContainer.execute", new_callable=AsyncMock
        ) as after_mock:
            result = await scene_handler_wrapper(event_update_mock, **kwargs)

            # Check whether handler is called with correct arguments
            handler_mock.assert_called_once_with(ANY, event_update_mock, **kwargs)

            # Check whether after_mock is called
            after_mock.assert_called_once_with(ANY)

            # Check whether result is correct
            assert result == 42

    def test_scene_handler_wrapper_str(self):
        # Mock objects
        scene_mock = AsyncMock(spec=Scene)
        handler_mock = AsyncMock()
        after_mock = AsyncMock()  # Implement this according to your After type

        scene_handler_wrapper = SceneHandlerWrapper(scene_mock, handler_mock, after=after_mock)
        result = str(scene_handler_wrapper)

        assert result == f"SceneHandlerWrapper({handler_mock}, after={after_mock})"

    def test_await(self):
        class MyScene(Scene):
            pass

        handler_mock = AsyncMock()
        scene_handler_wrapper = SceneHandlerWrapper(MyScene, handler_mock)

        assert inspect.isawaitable(scene_handler_wrapper)

        assert hasattr(scene_handler_wrapper, "__await__")
        assert scene_handler_wrapper.__await__() is scene_handler_wrapper
