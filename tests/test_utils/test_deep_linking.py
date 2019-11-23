import pytest

from aiogram.utils.deep_linking import decode_payload, encode_payload, filter_payload
from aiogram.utils.deep_linking import get_start_link, get_startgroup_link
from tests.types import dataset

# enable asyncio mode
pytestmark = pytest.mark.asyncio

PAYLOADS = [
    'foo',
    'AAbbCCddEEff1122334455',
    'aaBBccDDeeFF5544332211',
    -12345678901234567890,
    12345678901234567890,
]

WRONG_PAYLOADS = [
    '@BotFather',
    'spaces spaces spaces',
    1234567890123456789.0,
]


@pytest.fixture(params=PAYLOADS, name='payload')
def payload_fixture(request):
    return request.param


@pytest.fixture(params=WRONG_PAYLOADS, name='wrong_payload')
def wrong_payload_fixture(request):
    return request.param


@pytest.fixture(autouse=True)
def get_bot_user_fixture(monkeypatch):
    """ Monkey patching of bot.me calling. """
    from aiogram.utils import deep_linking

    async def get_bot_user_mock():
        from aiogram.types import User
        return User(**dataset.USER)

    monkeypatch.setattr(deep_linking, '_get_bot_user', get_bot_user_mock)


class TestDeepLinking:
    async def test_get_start_link(self, payload):
        link = await get_start_link(payload)
        assert link == f'https://t.me/{dataset.USER["username"]}?start={payload}'

    async def test_wrong_symbols(self, wrong_payload):
        with pytest.raises(ValueError):
            await get_start_link(wrong_payload)

    async def test_get_startgroup_link(self, payload):
        link = await get_startgroup_link(payload)
        assert link == f'https://t.me/{dataset.USER["username"]}?startgroup={payload}'

    async def test_filter_encode_and_decode(self, payload):
        _payload = filter_payload(payload)
        encoded = encode_payload(_payload)
        decoded = decode_payload(encoded)
        assert decoded == str(payload)

    async def test_get_start_link_with_encoding(self, payload):
        # define link
        link = await get_start_link(payload, encode=True)

        # define reference link
        payload = filter_payload(payload)
        encoded_payload = encode_payload(payload)

        assert link == f'https://t.me/{dataset.USER["username"]}?start={encoded_payload}'
