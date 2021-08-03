import pytest
from async_lru import alru_cache

from aiogram.utils.deep_linking import (
    create_start_link,
    create_startgroup_link,
    decode_payload,
    encode_payload,
)
from tests.mocked_bot import MockedBot

PAYLOADS = [
    "foo",
    "AAbbCCddEEff1122334455",
    "aaBBccDDeeFF5544332211",
    -12345678901234567890,
    12345678901234567890,
]
WRONG_PAYLOADS = [
    "@BotFather",
    "Some:special$characters#=",
    "spaces spaces spaces",
    1234567890123456789.0,
]

pytestmark = pytest.mark.asyncio


@pytest.fixture(params=PAYLOADS, name="payload")
def payload_fixture(request):
    return request.param


@pytest.fixture(params=WRONG_PAYLOADS, name="wrong_payload")
def wrong_payload_fixture(request):
    return request.param


@pytest.fixture(autouse=True)
def get_bot_user_fixture(monkeypatch):
    """Monkey patching of bot.me calling."""

    @alru_cache()
    async def get_bot_user_mock(self):
        from aiogram.types import User

        return User(
            id=12345678,
            is_bot=True,
            first_name="FirstName",
            last_name="LastName",
            username="username",
            language_code="uk-UA",
        )

    monkeypatch.setattr(MockedBot, "me", get_bot_user_mock)


class TestDeepLinking:
    async def test_get_start_link(self, bot, payload):
        link = await create_start_link(bot=bot, payload=payload)
        assert link == f"https://t.me/username?start={payload}"

    async def test_wrong_symbols(self, bot, wrong_payload):
        with pytest.raises(ValueError):
            await create_start_link(bot, wrong_payload)

    async def test_get_startgroup_link(self, bot, payload):
        link = await create_startgroup_link(bot, payload)
        assert link == f"https://t.me/username?startgroup={payload}"

    async def test_filter_encode_and_decode(self, payload):
        encoded = encode_payload(payload)
        decoded = decode_payload(encoded)
        assert decoded == str(payload)

    async def test_get_start_link_with_encoding(self, bot, wrong_payload):
        # define link
        link = await create_start_link(bot, wrong_payload, encode=True)

        # define reference link
        encoded_payload = encode_payload(wrong_payload)

        assert link == f"https://t.me/username?start={encoded_payload}"

    async def test_64_len_payload(self, bot):
        payload = "p" * 64
        link = await create_start_link(bot, payload)
        assert link

    async def test_too_long_payload(self, bot):
        payload = "p" * 65
        print(payload, len(payload))
        with pytest.raises(ValueError):
            await create_start_link(bot, payload)
