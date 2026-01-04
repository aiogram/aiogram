import datetime

from aiogram.methods import SendVenue
from aiogram.types import Chat, Location, Message, Venue
from tests.mocked_bot import MockedBot


class TestSendVenue:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendVenue,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                venue=Venue(
                    location=Location(latitude=3.14, longitude=3.14),
                    title="Cupboard Under the Stairs",
                    address="Under the stairs, 4 Privet Drive, "
                    "Little Whinging, Surrey, England, Great Britain",
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_venue(
            chat_id=42,
            latitude=3.14,
            longitude=3.14,
            title="Cupboard Under the Stairs",
            address="Under the stairs, 4 Privet Drive, "
            "Little Whinging, Surrey, England, Great Britain",
        )
        bot.get_request()
        assert response == prepare_result.result
