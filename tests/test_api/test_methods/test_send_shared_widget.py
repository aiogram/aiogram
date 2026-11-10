import datetime

from aiogram.methods import SendSharedWidget
from aiogram.types import Chat, Message, Widget
from tests.mocked_bot import MockedBot


class TestSendSharedWidget:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendSharedWidget,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                widget=Widget(id="widget", html="<p>Test</p>"),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_shared_widget(chat_id=42, widget_id="widget")
        bot.get_request()
        assert response == prepare_result.result
