from aiogram.methods import EditSharedWidgetData
from tests.mocked_bot import MockedBot


class TestEditSharedWidgetData:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditSharedWidgetData, ok=True, result=True)

        response: bool = await bot.edit_shared_widget_data(widget_id="widget", public_data="data")
        bot.get_request()
        assert response == prepare_result.result
