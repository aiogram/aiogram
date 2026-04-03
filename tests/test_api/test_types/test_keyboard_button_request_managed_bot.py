from aiogram.types import KeyboardButtonRequestManagedBot


class TestKeyboardButtonRequestManagedBot:
    def test_required_fields(self):
        obj = KeyboardButtonRequestManagedBot(request_id=1)
        assert obj.request_id == 1
        assert obj.suggested_name is None
        assert obj.suggested_username is None

    def test_optional_fields(self):
        obj = KeyboardButtonRequestManagedBot(
            request_id=2,
            suggested_name="My Bot",
            suggested_username="my_bot",
        )
        assert obj.request_id == 2
        assert obj.suggested_name == "My Bot"
        assert obj.suggested_username == "my_bot"
