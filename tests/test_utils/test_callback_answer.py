from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aiogram.exceptions import CallbackAnswerException
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import CallbackQuery, User
from aiogram.utils.callback_answer import CallbackAnswer, CallbackAnswerMiddleware


class TestCallbackAnswer:
    @pytest.mark.parametrize(
        "name,value",
        [
            ["answered", True],
            ["answered", False],
            ["disabled", True],
            ["disabled", False],
            ["text", "test"],
            ["text", None],
            ["show_alert", True],
            ["show_alert", False],
            ["show_alert", None],
            ["url", "https://example.com"],
            ["url", None],
            ["cache_time", None],
            ["cache_time", 10],
        ],
    )
    def test_getters(self, name, value):
        kwargs = {
            "answered": False,
            name: value,
        }
        instance = CallbackAnswer(**kwargs)
        result = getattr(instance, name)
        assert result == value

    @pytest.mark.parametrize(
        "name,value",
        [
            ["disabled", True],
            ["disabled", False],
            ["text", None],
            ["text", ""],
            ["text", "test"],
            ["show_alert", None],
            ["show_alert", True],
            ["show_alert", False],
            ["url", None],
            ["url", "https://example.com"],
            ["cache_time", None],
            ["cache_time", 0],
            ["cache_time", 10],
        ],
    )
    def test_setter_allowed(self, name, value):
        instance = CallbackAnswer(answered=False)
        setattr(instance, name, value)
        assert getattr(instance, name) == value

    @pytest.mark.parametrize(
        "name",
        [
            "disabled",
            "text",
            "show_alert",
            "url",
            "cache_time",
        ],
    )
    def test_setter_blocked(self, name):
        instance = CallbackAnswer(answered=True)
        with pytest.raises(CallbackAnswerException):
            setattr(instance, name, "test")

    def test_disable(self):
        instance = CallbackAnswer(answered=False)
        assert not instance.disabled
        instance.disable()
        assert instance.disabled

    def test_str(self):
        instance = CallbackAnswer(answered=False, text="test")
        assert str(instance) == "CallbackAnswer(answered=False, disabled=False, text='test')"


class TestCallbackAnswerMiddleware:
    @pytest.mark.parametrize(
        "init_kwargs,flag_properties,expected",
        [
            [
                {},
                True,
                {
                    "answered": False,
                    "disabled": False,
                    "text": None,
                    "show_alert": None,
                    "url": None,
                    "cache_time": None,
                },
            ],
            [
                {
                    "pre": True,
                    "text": "test",
                    "show_alert": True,
                    "url": "https://example.com",
                    "cache_time": 5,
                },
                True,
                {
                    "answered": True,
                    "disabled": False,
                    "text": "test",
                    "show_alert": True,
                    "url": "https://example.com",
                    "cache_time": 5,
                },
            ],
            [
                {
                    "pre": False,
                    "text": "test",
                    "show_alert": True,
                    "url": "https://example.com",
                    "cache_time": 5,
                },
                {
                    "pre": True,
                    "disabled": True,
                    "text": "another test",
                    "show_alert": False,
                    "url": "https://example.com/game.html",
                    "cache_time": 10,
                },
                {
                    "answered": True,
                    "disabled": True,
                    "text": "another test",
                    "show_alert": False,
                    "url": "https://example.com/game.html",
                    "cache_time": 10,
                },
            ],
        ],
    )
    def test_construct_answer(self, init_kwargs, flag_properties, expected):
        middleware = CallbackAnswerMiddleware(**init_kwargs)
        callback_answer = middleware.construct_callback_answer(properties=flag_properties)
        for key, value in expected.items():
            assert getattr(callback_answer, key) == value

    def test_answer(self):
        middleware = CallbackAnswerMiddleware()
        event = CallbackQuery(
            id="1",
            from_user=User(id=42, first_name="Test", is_bot=False),
            chat_instance="test",
        )
        callback_answer = CallbackAnswer(
            answered=False,
            disabled=False,
            text="another test",
            show_alert=False,
            url="https://example.com/game.html",
            cache_time=10,
        )
        method = middleware.answer(event=event, callback_answer=callback_answer)

        assert isinstance(method, AnswerCallbackQuery)
        assert method.text == callback_answer.text
        assert method.show_alert == callback_answer.show_alert
        assert method.url == callback_answer.url
        assert method.cache_time == callback_answer.cache_time

    @pytest.mark.parametrize(
        "properties,expected_stack",
        [
            [{"answered": False}, ["handler", "answer"]],
            [{"answered": True}, ["answer", "handler"]],
            [{"disabled": True}, ["handler"]],
        ],
    )
    async def test_call(self, properties, expected_stack):
        stack = []
        event = CallbackQuery(
            id="1",
            from_user=User(id=42, first_name="Test", is_bot=False),
            chat_instance="test",
        )

        async def handler(*args, **kwargs):
            stack.append("handler")

        async def answer(*args, **kwargs):
            stack.append("answer")

        middleware = CallbackAnswerMiddleware()
        with (
            patch(
                "aiogram.utils.callback_answer.CallbackAnswerMiddleware.construct_callback_answer",
                new_callable=MagicMock,
                side_effect=lambda **kwargs: CallbackAnswer(**{"answered": False, **properties}),
            ),
            patch(
                "aiogram.utils.callback_answer.CallbackAnswerMiddleware.answer",
                new=answer,
            ),
        ):
            await middleware(handler, event, {})

        assert stack == expected_stack

    async def test_invalid_event_type(self):
        middleware = CallbackAnswerMiddleware()
        handler = AsyncMock()
        await middleware(handler, None, {})
        handler.assert_awaited()
