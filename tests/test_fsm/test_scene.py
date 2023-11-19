import inspect
import platform
from datetime import datetime
from unittest.mock import ANY, AsyncMock, patch

import pytest

from aiogram import Dispatcher, F, Router
from aiogram.dispatcher.event.bases import NextMiddlewareType
from aiogram.exceptions import SceneException
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import (
    ActionContainer,
    After,
    ObserverDecorator,
    ObserverMarker,
    Scene,
    SceneAction,
    SceneHandlerWrapper,
    SceneRegistry,
    ScenesManager,
    SceneWizard,
    _empty_handler,
    on,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Chat, Message, TelegramObject, Update
from tests.mocked_bot import MockedBot


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
    async def test_scene_handler_wrapper_call(self):
        class MyScene(Scene):
            pass

        async def handler_mock(*args, **kwargs):
            return 42

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

        # Check whether result is correct
        assert result == 42

    async def test_scene_handler_wrapper_call_with_after(self):
        class MyScene(Scene):
            pass

        async def handler_mock(*args, **kwargs):
            return 42

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

            # Check whether after_mock is called
            after_mock.assert_called_once_with(ANY)

            # Check whether result is correct
            assert result == 42

    def test_scene_handler_wrapper_str(self):
        class MyScene(Scene):
            pass

        async def handler_mock(*args, **kwargs):
            pass

        after = After.back()

        scene_handler_wrapper = SceneHandlerWrapper(MyScene, handler_mock, after=after)
        result = str(scene_handler_wrapper)

        assert result == f"SceneHandlerWrapper({MyScene}, {handler_mock}, after={after})"

    def test_await(self):
        class MyScene(Scene):
            pass

        async def handler_mock(*args, **kwargs):
            pass

        scene_handler_wrapper = SceneHandlerWrapper(MyScene, handler_mock)

        assert inspect.isawaitable(scene_handler_wrapper)

        assert hasattr(scene_handler_wrapper, "__await__")
        assert scene_handler_wrapper.__await__() is scene_handler_wrapper


class TestSceneRegistry:
    def test_scene_registry_initialization(self):
        router = Router()
        register_on_add = True

        registry = SceneRegistry(router, register_on_add)

        assert registry.router == router
        assert registry.register_on_add == register_on_add
        assert registry._scenes == {}

    def test_scene_registry_add_scene(self):
        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = "test_scene"

        registry = SceneRegistry(router, register_on_add)
        registry.add(MyScene)

        assert len(registry._scenes) == 1
        assert registry._scenes["test_scene"] == MyScene

    def test_scene_registry_add_scene_pass_router(self):
        class MyScene(Scene):
            pass

        router = Router()
        MyScene.__scene_config__.state = "test_scene"

        registry = SceneRegistry(router)
        registry.add(MyScene, router=router)

        assert len(registry._scenes) == 1
        assert registry._scenes["test_scene"] == MyScene

    def test_scene_registry_add_scene_already_exists(self):
        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = "test_scene"

        registry = SceneRegistry(router, register_on_add)
        registry.add(MyScene)

        with pytest.raises(SceneException):
            registry.add(MyScene)

    def test_scene_registry_add_scene_no_scenes(self):
        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = "test_scene"

        registry = SceneRegistry(router, register_on_add)
        registry._scenes = {}

        with pytest.raises(ValueError, match="At least one scene must be specified"):
            registry.add()

    def test_scene_registry_register(self):
        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = "test_scene"

        registry = SceneRegistry(router, register_on_add)
        registry.register(MyScene)

        assert len(registry._scenes) == 1
        assert registry._scenes["test_scene"] == MyScene

    def test_scene_registry_get_scene_if_scene_type_is_str(self):
        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = "test_scene"

        registry = SceneRegistry(router, register_on_add)
        registry.add(MyScene)

        retrieved_scene = registry.get("test_scene")

        assert retrieved_scene == MyScene

    def test_scene_registry_get_scene_if_scene_type_is_scene(self):
        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = "test_scene"

        registry = SceneRegistry(router, register_on_add)
        registry.add(MyScene)

        retrieved_scene = registry.get(MyScene)

        assert retrieved_scene == MyScene

    def test_scene_registry_get_scene_if_scene_state_is_state(self):
        class MyStates(StatesGroup):
            test_state = State()

        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = MyStates.test_state

        registry = SceneRegistry(router, register_on_add)
        registry.add(MyScene)

        retrieved_scene = registry.get(MyScene)

        assert retrieved_scene == MyScene

    def test_scene_registry_get_scene_if_scene_state_is_not_str(self):
        class MyScene(Scene):
            pass

        router = Router()
        register_on_add = True
        MyScene.__scene_config__.state = 42

        registry = SceneRegistry(router, register_on_add)
        registry.add(MyScene)

        with pytest.raises(SceneException, match="Scene must be a subclass of Scene or a string"):
            registry.get(MyScene)

    def test_scene_registry_get_scene_not_registered(self):
        router = Router()
        register_on_add = True

        registry = SceneRegistry(router, register_on_add)

        with pytest.raises(SceneException):
            registry.get("test_scene")

    def test_scene_registry_setup_middleware_with_dispatcher(self):
        router = Router()

        registry = SceneRegistry(router)

        dispatcher = Dispatcher()
        registry._setup_middleware(dispatcher)

        assert registry._update_middleware in dispatcher.update.outer_middleware

        for name, observer in dispatcher.observers.items():
            if name == "update":
                continue
            assert registry._update_middleware not in observer.outer_middleware

    def test_scene_registry_setup_middleware_with_router(self):
        inner_router = Router()

        registry = SceneRegistry(inner_router)

        outer_router = Router()
        registry._setup_middleware(outer_router)

        for name, observer in outer_router.observers.items():
            if name in ("update", "error"):
                continue
            assert registry._middleware in observer.outer_middleware

    @pytest.mark.asyncio
    async def test_scene_registry_update_middleware(self, bot: MockedBot):
        router = Router()
        registry = SceneRegistry(router)
        handler = AsyncMock(spec=NextMiddlewareType)
        event = Update(update_id=42, message=Message(
            message_id=42,
            text="test",
            date=datetime.now(),
            chat=Chat(id=42, type="private"),
        ))
        data = {"state": FSMContext(storage=MemoryStorage(),
                                    key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id))}

        result = await registry._update_middleware(handler, event, data)

        assert "scenes" in data
        assert isinstance(data["scenes"], ScenesManager)
        handler.assert_called_once_with(event, data)
        assert result == handler.return_value

    @pytest.mark.asyncio
    async def test_scene_registry_update_middleware_not_update(self, bot: MockedBot):
        router = Router()
        registry = SceneRegistry(router)
        handler = AsyncMock(spec=NextMiddlewareType)
        event = Message(
            message_id=42,
            text="test",
            date=datetime.now(),
            chat=Chat(id=42, type="private"),
        )
        data = {"state": FSMContext(storage=MemoryStorage(),
                                    key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id))}

        with pytest.raises(AssertionError, match="Event must be an Update instance"):
            await registry._update_middleware(handler, event, data)

    @pytest.mark.asyncio
    async def test_scene_registry_middleware(self, bot: MockedBot):
        router = Router()
        registry = SceneRegistry(router)
        handler = AsyncMock(spec=NextMiddlewareType)
        event = Update(update_id=42, message=Message(
            message_id=42,
            text="test",
            date=datetime.now(),
            chat=Chat(id=42, type="private"),
        ))
        data = {"state": FSMContext(storage=MemoryStorage(),
                                    key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)),
                "event_update": event}

        result = await registry._middleware(handler, event, data)

        assert "scenes" in data
        assert isinstance(data["scenes"], ScenesManager)
        handler.assert_called_once_with(event, data)
        assert result == handler.return_value
