import time

import pytest
from pydantic import TypeAdapter, ValidationError

from aiogram.types import InaccessibleMessage, MaybeInaccessibleMessageUnion, Message, Update

UNION = TypeAdapter(MaybeInaccessibleMessageUnion)
CHAT = {"id": 1, "type": "private"}


def _pinned_chain(depth: int) -> dict:
    # Every level validated as both members would double the work per level
    message = {"message_id": 1, "date": 1, "chat": CHAT}
    for _ in range(depth):
        pinned = {"message_id": 1, "date": 1, "chat": CHAT, "pinned_message": message}
        message = {"message_id": 1, "date": 1, "chat": {**CHAT, "pinned_message": pinned}}
    return {
        "update_id": 1,
        "message": {"message_id": 1, "date": 1, "chat": CHAT, "pinned_message": message},
    }


def _best_time(depth: int) -> float:
    update = _pinned_chain(depth)
    timings = []
    for _ in range(5):
        start = time.perf_counter()
        Update.model_validate(update)
        timings.append(time.perf_counter() - start)
    return min(timings)


class TestMaybeInaccessibleMessageUnion:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ({"message_id": 1, "date": 0, "chat": CHAT}, InaccessibleMessage),
            ({"message_id": 1, "date": 1, "chat": CHAT}, Message),
            (InaccessibleMessage(message_id=1, chat=CHAT), InaccessibleMessage),
            (Message(message_id=1, date=1, chat=CHAT), Message),
        ],
    )
    def test_member_is_selected_by_date(self, value, expected):
        assert type(UNION.validate_python(value)) is expected

    def test_only_selected_member_is_validated(self):
        with pytest.raises(ValidationError) as exc_info:
            UNION.validate_python({"message_id": 1, "date": 1, "chat": None})
        assert [error["loc"] for error in exc_info.value.errors()] == [("Message", "chat")]

    def test_nested_validation_is_linear(self):
        _best_time(1)  # warm up schema building
        # Doubling the depth roughly doubles the time; a smart union would square it
        assert _best_time(12) < _best_time(6) * 8
