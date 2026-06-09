from aiogram.types import ManagedBotCreated, User


class TestManagedBotCreated:
    def test_fields(self):
        bot_user = User(id=123, is_bot=True, first_name="TestBot")
        obj = ManagedBotCreated(bot=bot_user)
        assert obj.bot_user == bot_user
        assert obj.bot_user.id == 123
