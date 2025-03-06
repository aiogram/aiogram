import pytest

from aiogram.utils.deep_linking import create_start_link, create_startgroup_link, \
    create_startapp_link
from aiogram.utils.payload import decode_payload, encode_payload
from tests.mocked_bot import MockedBot

PAYLOADS = [
    "foo",
    "AAbbCCddEEff1122334455",
    "aaBBccDDeeFF5544332211",
    -12345678901234567890,
    12345678901234567890,
    "underscore_and-dash",
]
WRONG_PAYLOADS = [
    "@BotFather",
    "Some:special$characters#=",
    "spaces spaces spaces",
    1234567890123456789.0,
    "has`backtick",
]


@pytest.fixture(params=PAYLOADS, name="payload")
def payload_fixture(request):
    return request.param


@pytest.fixture(params=WRONG_PAYLOADS, name="wrong_payload")
def wrong_payload_fixture(request):
    return request.param


class TestDeepLinking:
    async def test_get_start_link(self, bot: MockedBot, payload: str):
        link = await create_start_link(bot=bot, payload=payload)
        assert link == f"https://t.me/tbot?start={payload}"

    async def test_wrong_symbols(self, bot: MockedBot, wrong_payload: str):
        with pytest.raises(ValueError):
            await create_start_link(bot, wrong_payload)

    async def test_get_startgroup_link(self, bot: MockedBot, payload: str):
        link = await create_startgroup_link(bot, payload)
        assert link == f"https://t.me/tbot?startgroup={payload}"

    async def test_get_startapp_link(self, bot: MockedBot, payload: str):
        link = await create_startapp_link(bot, payload)
        assert link == f"https://t.me/tbot?startapp={payload}"

    async def test_filter_encode_and_decode(self, payload: str):
        encoded = encode_payload(payload)
        decoded = decode_payload(encoded)
        assert decoded == str(payload)

    async def test_custom_encode_decode(self, payload: str):
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import pad, unpad

        class Cryptor:
            def __init__(self, key: str):
                self.key = key.encode("utf-8")
                self.mode = AES.MODE_ECB  # never use ECB in strong systems obviously
                self.size = 32

            @property
            def cipher(self):
                return AES.new(self.key, self.mode)

            def encrypt(self, data: bytes) -> bytes:
                return self.cipher.encrypt(pad(data, self.size))

            def decrypt(self, data: bytes) -> bytes:
                decrypted_data = self.cipher.decrypt(data)
                return unpad(decrypted_data, self.size)

        cryptor = Cryptor("abcdefghijklmnop")
        encoded_payload = encode_payload(payload, encoder=cryptor.encrypt)
        decoded_payload = decode_payload(encoded_payload, decoder=cryptor.decrypt)

        assert decoded_payload == str(payload)

    async def test_get_start_link_with_encoding(self, bot: MockedBot, wrong_payload: str):
        # define link
        link = await create_start_link(bot, wrong_payload, encode=True)

        # define reference link
        encoded_payload = encode_payload(wrong_payload)

        assert link == f"https://t.me/tbot?start={encoded_payload}"

    async def test_get_startapp_link_with_encoding(self, bot: MockedBot, wrong_payload: str):
        # define link
        link = await create_startapp_link(bot, wrong_payload, encode=True)

        # define reference link
        encoded_payload = encode_payload(wrong_payload)

        assert link == f"https://t.me/tbot?startapp={encoded_payload}"

    async def test_64_len_payload(self, bot: MockedBot):
        payload = "p" * 64
        link = await create_start_link(bot, payload)
        assert link

    async def test_too_long_payload(self, bot: MockedBot):
        payload = "p" * 65
        with pytest.raises(ValueError):
            await create_start_link(bot, payload)
