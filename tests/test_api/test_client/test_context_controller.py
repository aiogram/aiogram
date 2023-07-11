from aiogram.client.context_controller import BotContextController
from tests.mocked_bot import MockedBot


class MyModel(BotContextController):
    id: int


class TestBotContextController:
    def test_via_model_validate(self, bot: MockedBot):
        my_model = MyModel.model_validate({"id": 1}, context={"bot": bot})
        assert my_model.id == 1
        assert my_model._bot == bot

    def test_via_model_validate_none(self):
        my_model = MyModel.model_validate({"id": 1}, context={})
        assert my_model.id == 1
        assert my_model._bot is None

    def test_as(self, bot: MockedBot):
        my_model = MyModel(id=1).as_(bot)
        assert my_model.id == 1
        assert my_model._bot == bot

    def test_as_none(self):
        my_model = MyModel(id=1).as_(None)
        assert my_model.id == 1
        assert my_model._bot is None

    def test_replacement(self, bot: MockedBot):
        my_model = MyModel(id=1).as_(bot)
        assert my_model.id == 1
        assert my_model._bot == bot
        my_model = my_model.as_(None)
        assert my_model.id == 1
        assert my_model._bot is None
