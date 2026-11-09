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
                    gifts_from_channels=True,
                ),
            ),
        )

        response: ChatFullInfo = await bot.get_chat(chat_id=-42)
        bot.get_request()
        assert response == prepare_result.result

    async def test_usernames_property(self, bot: MockedBot):
        bot.add_result_for(
            GetChat,
            ok=True,
            result=ChatFullInfo(
                id=bot.id,
                type="private",
                accent_color_id=0,
                max_reaction_count=0,
                accepted_gift_types=AcceptedGiftTypes(
                    unlimited_gifts=False,
                    limited_gifts=False,
                    unique_gifts=False,
                    premium_subscription=False,
                    gifts_from_channels=False,
                ),
                active_usernames=["tbot_AI", "tbot"],
            ),
        )

        assert await bot.usernames() == ("tbot", "tbot_AI")
        request = bot.get_request()
        assert isinstance(request, GetChat)
        assert request.chat_id == bot.id

        assert await bot.usernames() == ("tbot", "tbot_AI")
        assert not bot.session.requests
