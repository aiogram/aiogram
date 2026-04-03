from aiogram.methods import SavePreparedKeyboardButton
from aiogram.types import KeyboardButton, KeyboardButtonRequestManagedBot, PreparedKeyboardButton
from tests.mocked_bot import MockedBot


class TestSavePreparedKeyboardButton:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SavePreparedKeyboardButton,
            ok=True,
            result=PreparedKeyboardButton(id="test-id"),
        )

        response: PreparedKeyboardButton = await bot.save_prepared_keyboard_button(
            user_id=42,
            button=KeyboardButton(
                text="Create bot",
                request_managed_bot=KeyboardButtonRequestManagedBot(request_id=1),
            ),
        )
        bot.get_request()
        assert response == prepare_result.result
