from aiogram.types import ManagedBotUpdated, User


class TestManagedBotUpdated:
    def test_fields(self):
        user = User(id=42, is_bot=False, first_name="Creator")
        bot_user = User(id=123, is_bot=True, first_name="TestBot")
        obj = ManagedBotUpdated(user=user, bot=bot_user)
        assert obj.user == user
        assert obj.bot_user == bot_user
