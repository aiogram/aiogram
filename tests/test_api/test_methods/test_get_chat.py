from aiogram.methods import GetChat
from aiogram.types import AcceptedGiftTypes, ChatFullInfo
from tests.mocked_bot import MockedBot


class TestGetChat:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChat,
            ok=True,
            result=ChatFullInfo(
                id=-42,
                type="channel",
                title="chat",
                accent_color_id=0,
                max_reaction_count=0,
                accepted_gift_types=AcceptedGiftTypes(
                    unlimited_gifts=True,
                    limited_gifts=True,
                    unique_gifts=True,
                    premium_subscription=True,
                ),
            ),
        )

        response: ChatFullInfo = await bot.get_chat(chat_id=-42)
        request = bot.get_request()
        assert response == prepare_result.result
