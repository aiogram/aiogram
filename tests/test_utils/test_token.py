from unittest.mock import patch

import pytest

from aiogram.utils.token import TokenValidationError, extract_bot_id, validate_token

BOT_ID = 123456789
VALID_TOKEN = "123456789:AABBCCDDEEFFaabbccddeeff-1234567890"
INVALID_TOKENS = [
    "123456789:AABBCCDDEEFFaabbccddeeff 123456789",  # space is exists
    "ABC:AABBCCDDEEFFaabbccddeeff123456789",  # left part is not digit
    ":AABBCCDDEEFFaabbccddeeff123456789",  # there is no left part
    "123456789:",  # there is no right part
    "ABC AABBCCDDEEFFaabbccddeeff123456789",  # there is no ':' separator
    None,  # is None
    12345678,  # is digit
    (42, "TEST"),  # is tuple
]


@pytest.fixture(params=INVALID_TOKENS, name="invalid_token")
def invalid_token_fixture(request):
    return request.param


class TestCheckToken:
    def test_valid(self):
        assert validate_token(VALID_TOKEN) is True

    def test_invalid_token(self, invalid_token):
        with pytest.raises(TokenValidationError):
            validate_token(invalid_token)


class TestExtractBotId:
    def test_extract_bot_id(self):
        with patch("aiogram.utils.token.validate_token") as mocked_validate_token:
            result = extract_bot_id(VALID_TOKEN)

            mocked_validate_token.assert_called_once_with(VALID_TOKEN)
            assert result == BOT_ID
