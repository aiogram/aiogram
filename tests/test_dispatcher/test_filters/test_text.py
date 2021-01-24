import datetime
from itertools import permutations
from typing import Sequence, Type

import pytest
from pydantic import ValidationError

from aiogram.api.types import CallbackQuery, Chat, InlineQuery, Poll, PollOption, User, Message
from aiogram.dispatcher.filters import BUILTIN_FILTERS
from aiogram.dispatcher.filters.text import Text
from tests.factories.message import MessageFactory


class TestText:
    def test_default_for_observer(self):
        registered_for = {
            update_type for update_type, filters in BUILTIN_FILTERS.items() if Text in filters
        }
        assert registered_for == {
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "inline_query",
            "callback_query",
        }

    def test_validator_not_enough_arguments(self):
        with pytest.raises(ValidationError):
            Text()
        with pytest.raises(ValidationError):
            Text(text_ignore_case=True)

    @pytest.mark.parametrize(
        "first,last",
        permutations(["text", "text_contains", "text_startswith", "text_endswith"], 2),
    )
    @pytest.mark.parametrize("ignore_case", [True, False])
    def test_validator_too_few_arguments(self, first, last, ignore_case):
        kwargs = {first: "test", last: "test"}
        if ignore_case:
            kwargs["text_ignore_case"] = True

        with pytest.raises(ValidationError):
            Text(**kwargs)

    @pytest.mark.parametrize(
        "argument", ["text", "text_contains", "text_startswith", "text_endswith"]
    )
    @pytest.mark.parametrize("input_type", [str, list, tuple])
    def test_validator_convert_to_list(self, argument: str, input_type: Type):
        text = Text(**{argument: input_type("test")})
        assert hasattr(text, argument)
        assert isinstance(getattr(text, argument), Sequence)

    @pytest.mark.parametrize(
        "argument,ignore_case,input_value,update_type,result",
        [
            ["text", False, "test", MessageFactory(text=""), False,],
            [
                "text",
                False,
                "test",
                MessageFactory(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="",
                    caption="test",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            ["text", False, "test", MessageFactory(text="test"), True,],
            ["text", True, "TEst", MessageFactory(text="tesT"), True,],
            ["text", False, "TEst", MessageFactory(text="tesT"), False,],
            ["text_startswith", False, "test", MessageFactory(text="test case"), True,],
            ["text_endswith", False, "case", MessageFactory(text="test case"), True,],
            ["text_contains", False, " ", MessageFactory(text="test case"), True,],
            [
                "text_startswith",
                True,
                "question",
                MessageFactory(
                    text="",
                    poll=Poll(
                        id="poll id",
                        question="Question?",
                        options=[PollOption(text="A", voter_count=0)],
                        is_closed=False,
                        is_anonymous=False,
                        type="regular",
                        allows_multiple_answers=False,
                        total_voter_count=0,
                    ),
                ),
                True,
            ],
            [
                "text_startswith",
                True,
                "callback:",
                CallbackQuery(
                    id="query id",
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                    chat_instance="instance",
                    data="callback:data",
                ),
                True,
            ],
            [
                "text_startswith",
                True,
                "query",
                InlineQuery(
                    id="query id",
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                    query="query line",
                    offset="offset",
                ),
                True,
            ],
            [
                "text",
                True,
                "question",
                Poll(
                    id="poll id",
                    question="Question",
                    options=[PollOption(text="A", voter_count=0)],
                    is_closed=False,
                    is_anonymous=False,
                    type="regular",
                    allows_multiple_answers=False,
                    total_voter_count=0,
                ),
                True,
            ],
            [
                "text",
                True,
                ["question", "another question"],
                Poll(
                    id="poll id",
                    question="Another question",
                    options=[PollOption(text="A", voter_count=0)],
                    is_closed=False,
                    is_anonymous=False,
                    type="quiz",
                    allows_multiple_answers=False,
                    total_voter_count=0,
                    correct_option_id=0,
                ),
                True,
            ],
            ["text", True, ["question", "another question"], object(), False],
        ],
    )
    @pytest.mark.asyncio
    async def test_check_text(self, argument, ignore_case, input_value, result, update_type):
        text = Text(**{argument: input_value}, text_ignore_case=ignore_case)
        assert await text(obj=update_type) is result
