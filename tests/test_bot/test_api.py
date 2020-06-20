import pytest

from aiogram.bot.api import check_token
from aiogram.utils.exceptions import ValidationError

VALID_TOKEN = '123456789:AABBCCDDEEFFaabbccddeeff-1234567890'
INVALID_TOKENS = [
    '123456789:AABBCCDDEEFFaabbccddeeff 123456789',  # space is exists
    'ABC:AABBCCDDEEFFaabbccddeeff123456789',  # left part is not digit
    ':AABBCCDDEEFFaabbccddeeff123456789',  # there is no left part
    '123456789:',  # there is no right part
    'ABC AABBCCDDEEFFaabbccddeeff123456789',  # there is no ':' separator
    None,  # is None
    12345678,  # is digit
    {},  # is dict
    [],  # is dict
]


@pytest.fixture(params=INVALID_TOKENS, name='invalid_token')
def invalid_token_fixture(request):
    return request.param


class TestCheckToken:

    def test_valid(self):
        assert check_token(VALID_TOKEN) is True

    def test_invalid_token(self, invalid_token):
        with pytest.raises(ValidationError):
            check_token(invalid_token)
