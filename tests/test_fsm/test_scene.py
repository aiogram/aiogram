import pytest

from aiogram import F
from aiogram.fsm.scene import (
    on,
    ObserverMarker,
    ObserverDecorator,
    After,
    SceneAction,
    _empty_handler,
)


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
        decorator = ObserverDecorator("test", F.test)

        def handler():
            pass

        wrapped = decorator(handler)
        assert wrapped is not None
        assert not hasattr(wrapped, "__aiogram_handler__")
        assert hasattr(wrapped, "__aiogram_action__")

        assert isinstance(wrapped.__aiogram_action__, dict)
        assert len(wrapped.__aiogram_action__) == 1
        assert "test" in wrapped.__aiogram_action__
        assert wrapped.__aiogram_action__["test"]
