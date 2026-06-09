from aiogram.types import PreparedKeyboardButton


class TestPreparedKeyboardButton:
    def test_fields(self):
        obj = PreparedKeyboardButton(id="abc123")
        assert obj.id == "abc123"
