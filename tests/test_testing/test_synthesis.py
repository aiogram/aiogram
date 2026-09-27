import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union

import pytest
from pydantic import BaseModel

from aiogram import methods
from aiogram.methods.base import TelegramMethod
from aiogram.test.synthesis import (
    SynthesisContext,
    SynthesisError,
    annotation_accepts,
    synthesize,
    synthesize_result,
)
from aiogram.types import BusinessConnection, Chat, Message, User


def all_methods() -> list[type[TelegramMethod[Any]]]:
    found = {
        candidate
        for candidate in vars(methods).values()
        if isinstance(candidate, type)
        and issubclass(candidate, TelegramMethod)
        and candidate is not TelegramMethod
    }
    return sorted(found, key=lambda item: item.__name__)


class Colour(str, Enum):
    RED = "red"
    BLUE = "blue"


class Node(BaseModel):
    child: "Node"


Node.model_rebuild()


class TestEveryBotApiReturnType:
    """
    The guard that lets a Bot API bump land without touching the toolkit.

    A newly generated method whose return type the synthesizer cannot fill fails here,
    in aiogram's own CI, instead of in a user's test suite.
    """

    @pytest.mark.parametrize("method", all_methods(), ids=lambda item: item.__name__)
    def test_result_can_be_synthesized(self, method):
        result = synthesize_result(method.__returning__, SynthesisContext())

        assert result is not None or method.__returning__ is type(None)


class TestScalars:
    @pytest.mark.parametrize(
        ("annotation", "expected"),
        [
            (bool, True),
            (float, 1.0),
            (bytes, b""),
            (datetime.timedelta, datetime.timedelta(0)),
            (Colour, "red"),
            (Literal["a", "b"], "a"),
            (list[int], []),
            (dict[str, int], {}),
            (Any, None),
        ],
    )
    def test_values(self, annotation, expected):
        assert synthesize(annotation, SynthesisContext()) == expected

    def test_int_uses_a_counter(self):
        context = SynthesisContext()

        assert [synthesize(int, context), synthesize(int, context)] == [1, 2]

    def test_str_uses_the_field_name(self):
        assert synthesize(str, SynthesisContext(), name="chat_instance") == "chat_instance"

    def test_datetime_uses_the_context_date(self):
        moment = datetime.datetime(2030, 5, 5, tzinfo=datetime.timezone.utc)

        assert synthesize(datetime.datetime, SynthesisContext(date=moment)) == moment


class TestUnions:
    def test_optional_picks_the_concrete_member(self):
        assert synthesize(Optional[int], SynthesisContext()) == 1

    def test_union_picks_the_first_member(self):
        assert synthesize(Union[bool, int], SynthesisContext()) is True

    def test_pep604_union(self):
        assert synthesize(bool | None, SynthesisContext()) is True


class TestModels:
    def test_required_fields_are_filled(self):
        message = synthesize(Message, SynthesisContext())

        assert isinstance(message, Message)
        assert message.message_id
        assert message.chat is not None

    def test_seeded_chat_and_user(self):
        chat = Chat(id=-1, type="group", title="Team")
        user = User(id=7, is_bot=False, first_name="Alice")

        message = synthesize(Message, SynthesisContext(chat=chat, user=user))

        assert message.chat is chat

    def test_seeded_user_field(self):
        user = User(id=7, is_bot=False, first_name="Alice")

        connection = synthesize(BusinessConnection, SynthesisContext(user=user))

        assert connection.user is user

    def test_seeds_are_ignored_when_absent(self):
        message = synthesize(Message, SynthesisContext(chat=None))

        assert message.chat.id


class TestAnnotationAccepts:
    def test_plain_type(self):
        assert annotation_accepts(Chat, Chat)
        assert not annotation_accepts(int, Chat)

    def test_union_member(self):
        assert annotation_accepts(Chat | None, Chat)
        assert not annotation_accepts(int | None, Chat)

    def test_anything_else(self):
        assert not annotation_accepts("not-a-type", Chat)


class TestFailures:
    def test_recursive_required_field(self):
        with pytest.raises(SynthesisError, match="recursive required field chain"):
            synthesize(Node, SynthesisContext())

    def test_unsupported_class(self):
        with pytest.raises(SynthesisError, match="Cannot synthesize"):
            synthesize(object, SynthesisContext())

    def test_unsupported_annotation(self):
        with pytest.raises(SynthesisError, match="Cannot synthesize"):
            synthesize("not-a-type", SynthesisContext())
