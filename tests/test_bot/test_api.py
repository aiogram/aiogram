import pytest

from aiogram.bot.api import check_token
from aiogram.utils.exceptions import ValidationError

VALID_TOKEN = "123456789:AABBCCDDEEFFaabbccddeeff-1234567890"
INVALID_TOKEN = "123456789:AABBCCDDEEFFaabbccddeeff 123456789"  # Space in token and wrong length


class Test_check_token:
    def test_valid(self):
        assert check_token(VALID_TOKEN) is True

    def test_invalid_token(self):
        with pytest.raises(ValidationError):
            check_token(INVALID_TOKEN)
