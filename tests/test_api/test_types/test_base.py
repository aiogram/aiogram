import pytest
from pydantic import ValidationError

from aiogram.types import Update

CHAT = {"id": 1, "type": "private"}
PHOTO = {"file_id": "id", "file_unique_id": "uid", "width": 1, "height": 1}


def _update(depth: int = 0, **content) -> dict:
    message = {"message_id": 1, "date": 1, "chat": CHAT, **content}
    for _ in range(depth):
        message = {"message_id": 1, "date": 1, "chat": CHAT, "reply_to_message": message}
    return {"update_id": 1, "message": message}


class TestFailFastLists:
    def test_valid_lists_are_parsed(self):
        update = Update.model_validate(_update(photo=[PHOTO] * 3))
        assert len(update.message.photo) == 3

    @pytest.mark.parametrize("depth", [0, 50])
    @pytest.mark.parametrize(
        "content",
        [
            {"photo": [PHOTO, "x", "x"]},
            {"entities": [1] * 1000},
            {"new_chat_members": [None] * 1000},
            {"reply_markup": {"inline_keyboard": [[1] * 100] * 10}},
            {
                "chat_background_set": {
                    "type": {
                        "type": "fill",
                        "fill": {"type": "freeform_gradient", "colors": [""] * 1000},
                        "dark_theme_dimming": 0,
                    }
                }
            },
        ],
    )
    def test_list_stops_at_first_invalid_item(self, content: dict, depth: int):
        with pytest.raises(ValidationError) as exc_info:
            Update.model_validate(_update(depth, **content))
        assert exc_info.value.error_count() == 1
