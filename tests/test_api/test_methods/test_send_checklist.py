import datetime

from aiogram.methods import SendChecklist
from aiogram.types import Chat, InputChecklist, InputChecklistTask, Message
from tests.mocked_bot import MockedBot


class TestSendChecklist:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendChecklist,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                chat=Chat(id=42, type="private"),
            ),
        )

        checklist = InputChecklist(
            title="Test Checklist",
            tasks=[
                InputChecklistTask(id=1, text="Task 1"),
                InputChecklistTask(id=2, text="Task 2"),
            ],
        )

        response: Message = await bot.send_checklist(
            business_connection_id="test_connection",
            chat_id=42,
            checklist=checklist,
        )
        request = bot.get_request()
        assert response == prepare_result.result
