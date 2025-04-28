import inspect
from datetime import datetime
from unittest.mock import ANY, AsyncMock, patch

import pytest

from aiogram import Dispatcher, F, Router
from aiogram.dispatcher.event.bases import NextMiddlewareType
from aiogram.enums import UpdateType
from aiogram.exceptions import SceneException
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import (
    ActionContainer,
    After,
    HandlerContainer,
    HistoryManager,
    ObserverDecorator,
    ObserverMarker,
    Scene,
    SceneAction,
    SceneConfig,
    SceneHandlerWrapper,
    SceneRegistry,
    ScenesManager,
    SceneWizard,
    _empty_handler,
    on,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage, MemoryStorageRecord
from aiogram.types import Chat, Message, Update
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


class TestHistoryManager:
    async def test_history_manager_push(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state)

        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)

        history_data = await history_manager._history_state.get_data()
        assert history_data.get("history") == [{"state": "test_state", "data": data}]

    async def test_history_manager_push_if_history_overflow(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state, size=2)

        states = ["test_state", "test_state2", "test_state3", "test_state4"]
        data = {"test_data": "test_data"}
        for state in states:
            await history_manager.push(state, data)

        history_data = await history_manager._history_state.get_data()
        assert history_data.get("history") == [
            {"state": "test_state3", "data": data},
            {"state": "test_state4", "data": data},
        ]

    async def test_history_manager_pop(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state)

        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)
        await history_manager.push("test_state2", data)

        record = await history_manager.pop()
        history_data = await history_manager._history_state.get_data()

        assert isinstance(record, MemoryStorageRecord)
        assert record == MemoryStorageRecord(state="test_state2", data=data)
        assert history_data.get("history") == [{"state": "test_state", "data": data}]

    async def test_history_manager_pop_if_history_empty(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state)

        record = await history_manager.pop()
        assert record is None

    async def test_history_manager_pop_if_history_become_empty_after_pop(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state)

        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)

        await history_manager.pop()

        assert await history_manager._history_state.get_data() == {}

    async def test_history_manager_get(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state)

        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)

        record = await history_manager.get()

        assert isinstance(record, MemoryStorageRecord)
        assert record == MemoryStorageRecord(state="test_state", data=data)

    async def test_history_manager_get_if_history_empty(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state)

        record = await history_manager.get()
        assert record is None

    async def test_history_manager_all(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager_size = 10
        history_manager = HistoryManager(state=state, size=history_manager_size)

        data = {"test_data": "test_data"}
        for i in range(history_manager_size):
            await history_manager.push(f"test_state{i}", data)

        records = await history_manager.all()

        assert isinstance(records, list)
        assert len(records) == history_manager_size
        assert all(isinstance(record, MemoryStorageRecord) for record in records)

    async def test_history_manager_all_if_history_empty(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )
        history_manager = HistoryManager(state=state)

        records = await history_manager.all()
        assert records == []

    async def test_history_manager_clear(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )

        history_manager = HistoryManager(state=state)
        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)

        await history_manager.clear()

        assert await history_manager._history_state.get_data() == {}

    async def test_history_manager_snapshot(self):
        state = FSMContext(
            storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
        )

        history_manager = HistoryManager(state=state)
        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)

        await history_manager.snapshot()

        assert await history_manager._history_state.get_data() == {
            "history": [
                {"state": "test_state", "data": data},
                {
                    "state": await history_manager._state.get_state(),
                    "data": await history_manager._state.get_data(),
                },
            ]
        }

    async def test_history_manager_set_state(self):
        state_mock = AsyncMock(spec=FSMContext)
        state_mock.storage = MemoryStorage()
        state_mock.key = StorageKey(bot_id=42, chat_id=-42, user_id=42)
        state_mock.set_state = AsyncMock()
        state_mock.set_data = AsyncMock()

        history_manager = HistoryManager(state=state_mock)
        history_manager._state = state_mock

        state = "test_state"
        data = {"test_data": "test_data"}
        await history_manager._set_state(state, data)

        state_mock.set_state.assert_called_once_with(state)
        state_mock.set_data.assert_called_once_with(data)

    async def test_history_manager_rollback(self):
        history_manager = HistoryManager(
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
            )
        )

        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)
        await history_manager.push("test_state2", data)

        record = await history_manager.get()
        assert record == MemoryStorageRecord(state="test_state2", data=data)

        await history_manager.rollback()

        record = await history_manager.get()
        assert record == MemoryStorageRecord(state="test_state", data=data)

    async def test_history_manager_rollback_if_not_previous_state(self):
        history_manager = HistoryManager(
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
            )
        )

        data = {"test_data": "test_data"}
        await history_manager.push("test_state", data)

        state = await history_manager.rollback()
        assert state == "test_state"

        state = await history_manager.rollback()
        assert state is None


class TestScene:
    def test_scene_subclass_initialisation(self):
        class ParentScene(Scene):
            @on.message(F.text)
            def parent_handler(self, *args, **kwargs):
                pass

            @on.message.enter(F.text)
            def parent_action(self, *args, **kwargs):
                pass

        class SubScene(
            ParentScene,
            state="sub_state",
            reset_data_on_enter=True,
            reset_history_on_enter=True,
            callback_query_without_state=True,
        ):
            general_handler = on.message(
                F.text.casefold() == "test", after=After.goto("sub_state")
            )

            @on.message(F.text)
            def sub_handler(self, *args, **kwargs):
                pass

            @on.message.exit()
            def sub_action(self, *args, **kwargs):
                pass

        # Assert __scene_config__ attributes are correctly set for SubScene
        assert isinstance(SubScene.__scene_config__, SceneConfig)
        assert SubScene.__scene_config__.state == "sub_state"
        assert SubScene.__scene_config__.reset_data_on_enter is True
        assert SubScene.__scene_config__.reset_history_on_enter is True
        assert SubScene.__scene_config__.callback_query_without_state is True

        # Assert handlers are correctly set
        assert len(SubScene.__scene_config__.handlers) == 3

        for handler in SubScene.__scene_config__.handlers:
            assert isinstance(handler, HandlerContainer)
            assert handler.name == "message"
            assert handler.handler in (
                ParentScene.parent_handler,
                SubScene.sub_handler,
                _empty_handler,
            )
            assert handler.filters == (F.text,)

        # Assert actions are correctly set
        assert len(SubScene.__scene_config__.actions) == 2

        enter_action = SubScene.__scene_config__.actions[SceneAction.enter]
        assert isinstance(enter_action, dict)
        assert "message" in enter_action
        assert enter_action["message"].callback == ParentScene.parent_action

        exit_action = SubScene.__scene_config__.actions[SceneAction.exit]
        assert isinstance(exit_action, dict)
        assert "message" in exit_action
        assert exit_action["message"].callback == SubScene.sub_action

    def test_scene_subclass_initialisation_bases_is_scene_subclass(self):
        class NotAScene:
            pass

        class MyScene(Scene, NotAScene):
            pass

        class TestClass(MyScene, NotAScene):
            pass

        assert MyScene in TestClass.__bases__
        assert NotAScene in TestClass.__bases__
        bases = [base for base in TestClass.__bases__ if not issubclass(base, Scene)]
        assert Scene not in bases
        assert NotAScene in bases

    def test_scene_add_to_router(self):
        class MyScene(Scene):
            @on.message(F.text)
            def test_handler(self, *args, **kwargs):
                pass

        router = Router()
        MyScene.add_to_router(router)

        assert len(router.observers["message"].handlers) == 1

    def test_scene_add_to_router_scene_with_callback_query_without_state(self):
        class MyScene(Scene, callback_query_without_state=True):
            @on.callback_query(F.data)
            def test_handler(self, *args, **kwargs):
                pass

        router = Router()
        MyScene.add_to_router(router)

        assert len(router.observers["callback_query"].handlers) == 1
        assert (
            StateFilter(MyScene.__scene_config__.state)
            not in router.observers["callback_query"].handlers[0].filters
        )

    def test_scene_as_handler(self):
        class MyScene(Scene):
            @on.message(F.text)
            def test_handler(self, *args, **kwargs):
                pass

        handler = MyScene.as_handler()

        router = Router()
        router.message.register(handler)
        assert router.observers["message"].handlers[0].callback == handler

    async def test_scene_as_handler_enter(self):
        class MyScene(Scene):
            @on.message.enter(F.text)
            def test_handler(self, *args, **kwargs):
                pass

        event = AsyncMock()

        scenes = ScenesManager(
            registry=SceneRegistry(Router()),
            update_type="message",
            event=event,
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
            ),
            data={},
        )
        scenes.enter = AsyncMock()

        kwargs = {"test_kwargs": "test_kwargs"}
        handler = MyScene.as_handler(**kwargs)
        await handler(event, scenes)

        scenes.enter.assert_called_once_with(MyScene, **kwargs)

    async def test_scene_as_handler_enter_with_middleware_data(self):
        """Test that middleware data is correctly passed to the scene when using as_handler()."""

        class MyScene(Scene):
            @on.message.enter()
            def test_handler(self, *args, **kwargs):
                pass

        event = AsyncMock()

        scenes = ScenesManager(
            registry=SceneRegistry(Router()),
            update_type="message",
            event=event,
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(bot_id=42, chat_id=-42, user_id=42)
            ),
            data={},
        )
        scenes.enter = AsyncMock()

        # Kwargs passed to as_handler
        handler_kwargs = {"handler_kwarg": "handler_value", "mixed_kwarg": "handler_value"}
        handler = MyScene.as_handler(**handler_kwargs)

        # Middleware data that would be passed to the handler
        middleware_data = {
            "middleware_data": "middleware_value",
            "mixed_kwarg": "middleware_value",
        }

        # Call the handler with middleware data
        await handler(event, scenes, **middleware_data)

        # Verify that both handler kwargs and middleware data are passed to scenes.enter
        expected_kwargs = {**handler_kwargs, **middleware_data}
        scenes.enter.assert_called_once_with(MyScene, **expected_kwargs)


class TestSceneWizard:
    async def test_scene_wizard_enter_with_reset_data_on_enter(self):
        class MyScene(Scene, reset_data_on_enter=True):
            pass

        scene_config_mock = AsyncMock()
        scene_config_mock.state = "test_state"

        state_mock = AsyncMock(spec=FSMContext)
        state_mock.set_state = AsyncMock()

        wizard = SceneWizard(
            scene_config=MyScene.__scene_config__,
            manager=AsyncMock(spec=ScenesManager),
            state=state_mock,
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        kwargs = {"test_kwargs": "test_kwargs"}
        wizard._on_action = AsyncMock()

        await wizard.enter(**kwargs)

        state_mock.set_data.assert_called_once_with({})
        state_mock.set_state.assert_called_once_with(MyScene.__scene_config__.state)
        wizard._on_action.assert_called_once_with(SceneAction.enter, **kwargs)

    async def test_scene_wizard_enter_with_reset_history_on_enter(self):
        class MyScene(Scene, reset_history_on_enter=True):
            pass

        state_mock = AsyncMock(spec=FSMContext)
        state_mock.set_state = AsyncMock()

        manager = AsyncMock(spec=ScenesManager)
        manager.history = AsyncMock(spec=HistoryManager)
        manager.history.clear = AsyncMock()

        wizard = SceneWizard(
            scene_config=MyScene.__scene_config__,
            manager=manager,
            state=state_mock,
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        kwargs = {"test_kwargs": "test_kwargs"}
        wizard._on_action = AsyncMock()

        await wizard.enter(**kwargs)

        manager.history.clear.assert_called_once()
        state_mock.set_state.assert_called_once_with(MyScene.__scene_config__.state)
        wizard._on_action.assert_called_once_with(SceneAction.enter, **kwargs)

    async def test_scene_wizard_leave_with_history(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.state = "test_state"

        manager = AsyncMock(spec=ScenesManager)
        manager.history = AsyncMock(spec=HistoryManager)
        manager.history.snapshot = AsyncMock()

        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=manager,
            state=AsyncMock(spec=FSMContext),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard._on_action = AsyncMock()

        kwargs = {"test_kwargs": "test_kwargs"}
        await wizard.leave(_with_history=False, **kwargs)

        manager.history.snapshot.assert_not_called()
        wizard._on_action.assert_called_once_with(SceneAction.leave, **kwargs)

    async def test_scene_wizard_leave_without_history(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.state = "test_state"

        manager = AsyncMock(spec=ScenesManager)
        manager.history = AsyncMock(spec=HistoryManager)
        manager.history.snapshot = AsyncMock()

        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=manager,
            state=AsyncMock(spec=FSMContext),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard._on_action = AsyncMock()

        kwargs = {"test_kwargs": "test_kwargs"}
        await wizard.leave(**kwargs)

        manager.history.snapshot.assert_called_once()
        wizard._on_action.assert_called_once_with(SceneAction.leave, **kwargs)

    async def test_scene_wizard_back(self):
        current_scene_config_mock = AsyncMock()
        current_scene_config_mock.state = "test_state"

        previous_scene_config_mock = AsyncMock()
        previous_scene_config_mock.state = "previous_test_state"

        previous_scene_mock = AsyncMock()
        previous_scene_mock.__scene_config__ = previous_scene_config_mock

        manager = AsyncMock(spec=ScenesManager)
        manager.history = AsyncMock(spec=HistoryManager)
        manager.history.rollback = AsyncMock(return_value=previous_scene_mock)
        manager.enter = AsyncMock()

        wizard = SceneWizard(
            scene_config=current_scene_config_mock,
            manager=manager,
            state=AsyncMock(spec=FSMContext),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard.leave = AsyncMock()

        kwargs = {"test_kwargs": "test_kwargs"}
        await wizard.back(**kwargs)

        wizard.leave.assert_called_once_with(_with_history=False, **kwargs)
        manager.history.rollback.assert_called_once()
        manager.enter.assert_called_once_with(previous_scene_mock, _check_active=False, **kwargs)

    async def test_scene_wizard_retake(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.state = "test_state"

        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=AsyncMock(spec=ScenesManager),
            state=AsyncMock(spec=FSMContext),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard.goto = AsyncMock()

        kwargs = {"test_kwargs": "test_kwargs"}
        await wizard.retake(**kwargs)

        wizard.goto.assert_called_once_with(scene_config_mock.state, **kwargs)

    async def test_scene_wizard_retake_exception(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.state = None

        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=AsyncMock(spec=ScenesManager),
            state=AsyncMock(spec=FSMContext),
            update_type="message",
            event=AsyncMock(),
            data={},
        )

        kwargs = {"test_kwargs": "test_kwargs"}

        with pytest.raises(AssertionError, match="Scene state is not specified"):
            await wizard.retake(**kwargs)

    async def test_scene_wizard_goto(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.state = "test_state"

        scene_mock = AsyncMock()
        scene_mock.__scene_config__ = scene_config_mock

        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=AsyncMock(spec=ScenesManager),
            state=AsyncMock(spec=FSMContext),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard.leave = AsyncMock()
        wizard.manager.enter = AsyncMock()

        kwargs = {"test_kwargs": "test_kwargs"}
        await wizard.goto(scene_mock, **kwargs)

        wizard.leave.assert_called_once_with(**kwargs)
        wizard.manager.enter.assert_called_once_with(scene_mock, _check_active=False, **kwargs)

    async def test_scene_wizard_on_action(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.actions = {SceneAction.enter: {"message": AsyncMock()}}
        scene_config_mock.state = "test_state"

        scene_mock = AsyncMock()

        event_mock = AsyncMock()
        event_mock.type = "message"

        data = {"test_data": "test_data"}
        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=event_mock,
            data=data,
        )
        wizard.scene = scene_mock

        kwargs = {"test_kwargs": "test_kwargs"}
        result = await wizard._on_action(SceneAction.enter, **kwargs)

        scene_config_mock.actions[SceneAction.enter]["message"].call.assert_called_once_with(
            scene_mock, event_mock, **{**data, **kwargs}
        )
        assert result is True

    async def test_scene_wizard_on_action_no_scene(self):
        wizard = SceneWizard(
            scene_config=AsyncMock(),
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=AsyncMock(),
            data={},
        )

        with pytest.raises(SceneException, match="Scene is not initialized"):
            await wizard._on_action(SceneAction.enter)

    async def test_scene_wizard_on_action_no_action_config(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.actions = {}
        scene_config_mock.state = "test_state"

        scene_mock = AsyncMock()

        event_mock = AsyncMock()
        event_mock.type = "message"

        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=event_mock,
            data={},
        )
        wizard.scene = scene_mock

        kwargs = {"test_kwargs": "test_kwargs"}
        result = await wizard._on_action(SceneAction.enter, **kwargs)

        assert result is False

    async def test_scene_wizard_on_action_event_type_not_in_action_config(self):
        scene_config_mock = AsyncMock()
        scene_config_mock.actions = {SceneAction.enter: {"test_update_type": AsyncMock()}}
        scene_config_mock.state = "test_state"

        event_mock = AsyncMock()
        event_mock.type = "message"

        wizard = SceneWizard(
            scene_config=scene_config_mock,
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=event_mock,
            data={},
        )
        wizard.scene = AsyncMock()

        kwargs = {"test_kwargs": "test_kwargs"}
        result = await wizard._on_action(SceneAction.enter, **kwargs)

        assert result is False

    async def test_scene_wizard_set_data(self):
        wizard = SceneWizard(
            scene_config=AsyncMock(),
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard.state.set_data = AsyncMock()

        data = {"test_key": "test_value"}
        await wizard.set_data(data)

        wizard.state.set_data.assert_called_once_with(data=data)

    async def test_scene_wizard_get_data(self):
        wizard = SceneWizard(
            scene_config=AsyncMock(),
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard.state.get_data = AsyncMock()

        await wizard.get_data()

        wizard.state.get_data.assert_called_once_with()

    async def test_scene_wizard_get_value_with_default(self):
        wizard = SceneWizard(
            scene_config=AsyncMock(),
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        args = ("test_key", "test_default")
        value = "test_value"
        wizard.state.get_value = AsyncMock(return_value=value)

        result = await wizard.get_value(*args)
        wizard.state.get_value.assert_called_once_with(*args)

        assert result == value

    async def test_scene_wizard_update_data_if_data(self):
        wizard = SceneWizard(
            scene_config=AsyncMock(),
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        data = {"test_key": "test_value"}
        kwargs = {"test_kwargs": "test_kwargs"}

        wizard.state.update_data = AsyncMock(return_value={**data, **kwargs})
        result = await wizard.update_data(data=data, **kwargs)

        wizard.state.update_data.assert_called_once_with(data={**data, **kwargs})
        assert result == {**data, **kwargs}

    async def test_scene_wizard_update_data_if_no_data(self):
        wizard = SceneWizard(
            scene_config=AsyncMock(),
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        data = None
        kwargs = {"test_kwargs": "test_kwargs"}

        wizard.state.update_data = AsyncMock(return_value={**kwargs})
        result = await wizard.update_data(data=data, **kwargs)

        wizard.state.update_data.assert_called_once_with(data=kwargs)
        assert result == {**kwargs}

    async def test_scene_wizard_clear_data(self):
        wizard = SceneWizard(
            scene_config=AsyncMock(),
            manager=AsyncMock(),
            state=AsyncMock(),
            update_type="message",
            event=AsyncMock(),
            data={},
        )
        wizard.set_data = AsyncMock()

        await wizard.clear_data()

        wizard.set_data.assert_called_once_with({})


class TestScenesManager:
    async def test_scenes_manager_get_scene(self, bot: MockedBot):
        class MyScene(Scene):
            pass

        router = Router()

        registry = SceneRegistry(router)
        registry.add(MyScene)

        scenes_manager = ScenesManager(
            registry=registry,
            update_type="message",
            event=Update(
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
            ),
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            data={},
        )

        scene = await scenes_manager._get_scene(MyScene)
        assert isinstance(scene, MyScene)
        assert isinstance(scene.wizard, SceneWizard)
        assert scene.wizard.scene_config == MyScene.__scene_config__
        assert scene.wizard.manager == scenes_manager
        assert scene.wizard.update_type == "message"
        assert scene.wizard.data == {}

    async def test_scenes_manager_get_active_scene(self, bot: MockedBot):
        class TestScene(Scene):
            pass

        class TestScene2(Scene, state="test_state2"):
            pass

        registry = SceneRegistry(Router())
        registry.add(TestScene, TestScene2)

        manager = ScenesManager(
            registry,
            update_type="message",
            event=Update(
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
            ),
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            data={},
        )

        scene = await manager._get_active_scene()
        assert isinstance(scene, TestScene)

        await manager.enter(TestScene2)
        scene = await manager._get_active_scene()
        assert isinstance(scene, TestScene2)

    async def test_scenes_manager_get_active_scene_with_scene_exception(self, bot: MockedBot):
        registry = SceneRegistry(Router())

        manager = ScenesManager(
            registry,
            update_type="message",
            event=Update(
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
            ),
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            data={},
        )

        scene = await manager._get_active_scene()

        assert scene is None

    async def test_scenes_manager_enter_with_scene_type_none(self, bot: MockedBot):
        registry = SceneRegistry(Router())

        manager = ScenesManager(
            registry,
            update_type="message",
            event=Update(
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
            ),
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            data={},
        )

        assert await manager.enter(None) is None

    async def test_scenes_manager_enter_with_scene_exception(self, bot: MockedBot):
        registry = SceneRegistry(Router())

        manager = ScenesManager(
            registry,
            update_type="message",
            event=Update(
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
            ),
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            data={},
        )

        scene = "invalid_scene"
        with pytest.raises(SceneException, match=f"Scene {scene!r} is not registered"):
            await manager.enter(scene)

    async def test_scenes_manager_close_if_active_scene(self, bot: MockedBot):
        class TestScene(Scene):
            pass

        registry = SceneRegistry(Router())
        registry.add(TestScene)

        manager = ScenesManager(
            registry,
            update_type="message",
            event=Update(
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
            ),
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            data={},
        )

        manager._get_active_scene = AsyncMock(
            return_value=TestScene(
                SceneWizard(
                    scene_config=TestScene.__scene_config__,
                    manager=manager,
                    state=manager.state,
                    update_type="message",
                    event=manager.event,
                    data={},
                )
            )
        )
        manager._get_active_scene.return_value.wizard.exit = AsyncMock()

        await manager.close()

        manager._get_active_scene.assert_called_once()
        manager._get_active_scene.return_value.wizard.exit.assert_called_once()

    async def test_scenes_manager_close_if_no_active_scene(self, bot: MockedBot):
        registry = SceneRegistry(Router())

        manager = ScenesManager(
            registry,
            update_type="message",
            event=Update(
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
            ),
            state=FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            data={},
        )

        manager._get_active_scene = AsyncMock(return_value=None)

        result = await manager.close()

        manager._get_active_scene.assert_called_once()

        assert result is None


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

        with pytest.raises(
            SceneException, match="Scene must be a subclass of Scene, State or a string"
        ):
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

    async def test_scene_registry_update_middleware(self, bot: MockedBot):
        router = Router()
        registry = SceneRegistry(router)
        handler = AsyncMock(spec=NextMiddlewareType)
        event = Update(
            update_id=42,
            message=Message(
                message_id=42,
                text="test",
                date=datetime.now(),
                chat=Chat(id=42, type="private"),
            ),
        )
        data = {
            "state": FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            )
        }

        result = await registry._update_middleware(handler, event, data)

        assert "scenes" in data
        assert isinstance(data["scenes"], ScenesManager)
        handler.assert_called_once_with(event, data)
        assert result == handler.return_value

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
        data = {
            "state": FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            )
        }

        with pytest.raises(AssertionError, match="Event must be an Update instance"):
            await registry._update_middleware(handler, event, data)

    async def test_scene_registry_middleware(self, bot: MockedBot):
        router = Router()
        registry = SceneRegistry(router)
        handler = AsyncMock(spec=NextMiddlewareType)
        event = Update(
            update_id=42,
            message=Message(
                message_id=42,
                text="test",
                date=datetime.now(),
                chat=Chat(id=42, type="private"),
            ),
        )
        data = {
            "state": FSMContext(
                storage=MemoryStorage(), key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)
            ),
            "event_update": event,
        }

        result = await registry._middleware(handler, event, data)

        assert "scenes" in data
        assert isinstance(data["scenes"], ScenesManager)
        handler.assert_called_once_with(event, data)
        assert result == handler.return_value


class TestSceneInheritance:
    def test_inherit_handlers(self):
        class ParentScene(Scene):
            @on.message(Command("exit"))
            async def command_exit(self, message: Message) -> None:
                pass

        class ChildScene(ParentScene):
            pass

        assert len(ParentScene.__scene_config__.handlers) == 1
        assert len(ChildScene.__scene_config__.handlers) == 1

        parent_command_handler = ParentScene.__scene_config__.handlers[0]
        child_command_handler = ChildScene.__scene_config__.handlers[0]

        assert parent_command_handler.handler is ParentScene.command_exit
        assert child_command_handler.handler is ParentScene.command_exit

    def test_override_handlers(self):
        class ParentScene(Scene):
            @on.message(Command("exit"))
            async def command_exit(self, message: Message) -> int:
                return 1

        class ChildScene(ParentScene):
            @on.message(Command("exit"))
            async def command_exit(self, message: Message) -> int:
                return 2

        assert len(ParentScene.__scene_config__.handlers) == 1
        assert len(ChildScene.__scene_config__.handlers) == 1

        parent_command_handler = ParentScene.__scene_config__.handlers[0]
        child_command_handler = ChildScene.__scene_config__.handlers[0]

        assert parent_command_handler.handler is ParentScene.command_exit
        assert child_command_handler.handler is not ParentScene.command_exit
        assert child_command_handler.handler is ChildScene.command_exit

    def test_inherit_actions(self):
        class ParentScene(Scene):
            @on.message.enter()
            async def on_enter(self, message: Message) -> None:
                pass

        class ChildScene(ParentScene):
            pass

        parent_enter_action = ParentScene.__scene_config__.actions[SceneAction.enter][
            UpdateType.MESSAGE
        ]
        child_enter_action = ChildScene.__scene_config__.actions[SceneAction.enter][
            UpdateType.MESSAGE
        ]

        assert parent_enter_action.callback is ParentScene.on_enter
        assert child_enter_action.callback is ParentScene.on_enter
        assert child_enter_action.callback is ChildScene.on_enter

    def test_override_actions(self):
        class ParentScene(Scene):
            @on.message.enter()
            async def on_enter(self, message: Message) -> int:
                return 1

        class ChildScene(ParentScene):
            @on.message.enter()
            async def on_enter(self, message: Message) -> int:
                return 2

        parent_enter_action = ParentScene.__scene_config__.actions[SceneAction.enter][
            UpdateType.MESSAGE
        ]
        child_enter_action = ChildScene.__scene_config__.actions[SceneAction.enter][
            UpdateType.MESSAGE
        ]

        assert parent_enter_action.callback is ParentScene.on_enter
        assert child_enter_action.callback is not ParentScene.on_enter
        assert child_enter_action.callback is ChildScene.on_enter

    def test_override_non_function_handler_by_function(self):
        class ParentScene(Scene):
            do_exit = on.message(Command("exit"), after=After.exit)

        class ChildScene1(ParentScene):
            pass

        class ChildScene2(ParentScene):
            do_exit = on.message(Command("exit"), after=After.back)

        class ChildScene3(ParentScene):
            @on.message(Command("exit"), after=After.back)
            async def do_exit(self, message: Message) -> None:
                pass

        assert len(ParentScene.__scene_config__.handlers) == 1
        assert len(ChildScene1.__scene_config__.handlers) == 1
        assert len(ChildScene2.__scene_config__.handlers) == 1
        assert len(ChildScene3.__scene_config__.handlers) == 1

        parent_handler = ParentScene.__scene_config__.handlers[0]
        child_1_handler = ChildScene1.__scene_config__.handlers[0]
        child_2_handler = ChildScene2.__scene_config__.handlers[0]
        child_3_handler = ChildScene3.__scene_config__.handlers[0]

        assert child_1_handler.handler is parent_handler.handler
        assert child_1_handler.after == parent_handler.after
        assert child_1_handler.handler is _empty_handler

        assert child_2_handler.after != parent_handler.after
        assert child_2_handler.handler is _empty_handler

        assert child_3_handler.handler is not _empty_handler


def collect_handler_names(scene):
    return [handler.handler.__name__ for handler in scene.__scene_config__.handlers]


class TestSceneHandlersOrdering:
    def test_correct_ordering(self):
        class Scene1(Scene):
            @on.message()
            async def handler1(self, message: Message) -> None:
                pass

            @on.message()
            async def handler2(self, message: Message) -> None:
                pass

        class Scene2(Scene):
            @on.message()
            async def handler2(self, message: Message) -> None:
                pass

            @on.message()
            async def handler1(self, message: Message) -> None:
                pass

        assert collect_handler_names(Scene1) == ["handler1", "handler2"]
        assert collect_handler_names(Scene2) == ["handler2", "handler1"]

    def test_inherited_handlers_follow_mro_order(self):
        class Scene1(Scene):
            @on.message()
            async def handler1(self, message: Message) -> None:
                pass

            @on.message()
            async def handler2(self, message: Message) -> None:
                pass

        class Scene2(Scene1):
            @on.message()
            async def handler3(self, message: Message) -> None:
                pass

            @on.message()
            async def handler4(self, message: Message) -> None:
                pass

        assert collect_handler_names(Scene2) == ["handler3", "handler4", "handler1", "handler2"]

    def test_inherited_overwrite_follow_mro_order(self):
        class Scene1(Scene):
            @on.message()
            async def handler1(self, message: Message) -> None:
                pass

            @on.message()
            async def handler2(self, message: Message) -> None:
                pass

        class Scene2(Scene1):
            @on.message()
            async def handler2(self, message: Message) -> None:
                pass

            @on.message()
            async def handler3(self, message: Message) -> None:
                pass

        assert collect_handler_names(Scene2) == ["handler3", "handler1", "handler2"]
