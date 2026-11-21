from aiogram.methods import EditMessageWidgetData
from tests.mocked_bot import MockedBot


class TestEditMessageWidgetData:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageWidgetData, ok=True, result=True)

        response: bool = await bot.edit_message_widget_data(
            chat_id=42, message_id=42, public_data="data"
        )
        bot.get_request()
        assert response == prepare_result.result
