import datetime
from itertools import permutations
from typing import Sequence, Type

import pytest

from aiogram.filters import Text
from aiogram.types import (
    CallbackQuery,
    Chat,
    InlineQuery,
    Message,
    Poll,
    PollOption,
    User,
)


class TestText:
    @pytest.mark.parametrize(
        "kwargs",
        [
            {},
            {"ignore_case": True},
            {"ignore_case": False},
        ],
    )
    def test_not_enough_arguments(self, kwargs):
        with pytest.raises(ValueError):
            Text(**kwargs)

    @pytest.mark.parametrize(
        "first,last",
        permutations(["text", "contains", "startswith", "endswith"], 2),
    )
    @pytest.mark.parametrize("ignore_case", [True, False])
    def test_validator_too_few_arguments(self, first, last, ignore_case):
        kwargs = {first: "test", last: "test", "ignore_case": ignore_case}

        with pytest.raises(ValueError):
            Text(**kwargs)

    @pytest.mark.parametrize("argument", ["text", "contains", "startswith", "endswith"])
    @pytest.mark.parametrize("input_type", [str, list, tuple])
    def test_validator_convert_to_list(self, argument: str, input_type: Type):
        text = Text(**{argument: input_type("test")})
        assert hasattr(text, argument)
        assert isinstance(getattr(text, argument), Sequence)

    @pytest.mark.parametrize(
        "argument,ignore_case,input_value,update_type,result",
        [
            [
                "text",
                False,
                "test",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                False,
            ],
            [
                "text",
                False,
                "test",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    caption="test",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            [
                "text",
                False,
                "test",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="test",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            [
                "text",
                True,
                "TEst",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="tesT",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            [
                "text",
                False,
                "TEst",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="tesT",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                False,
            ],
            [
                "startswith",
                False,
                "test",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="test case",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            [
                "endswith",
                False,
                "case",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="test case",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            [
                "contains",
                False,
                " ",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="test case",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            [
                "startswith",
                True,
                "question",
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                True,
            ],
            [
                "startswith",
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
                "startswith",
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
    async def test_check_text(self, argument, ignore_case, input_value, result, update_type):
        text = Text(**{argument: input_value}, ignore_case=ignore_case)
        test = await text(update_type)
        assert test is result

    def test_str(self):
        text = Text("test")
        assert str(text) == "Text(text=['test'], ignore_case=False)"
