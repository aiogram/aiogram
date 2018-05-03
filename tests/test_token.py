import pytest

from aiogram.bot import api
from aiogram.utils import auth_widget, exceptions

VALID_TOKEN = '123456789:AABBCCDDEEFFaabbccddeeff-1234567890'
INVALID_TOKEN = '123456789:AABBCCDDEEFFaabbccddeeff 123456789'  # Space in token and wrong length

VALID_DATA = {
    'date': 1525385236,
    'first_name': 'Test',
    'last_name': 'User',
    'id': 123456789,
    'username': 'username',
    'hash': '69a9871558fbbe4cd0dbaba52fa1cc4f38315d3245b7504381a64139fb024b5b'
}
INVALID_DATA = {
    'date': 1525385237,
    'first_name': 'Test',
    'last_name': 'User',
    'id': 123456789,
    'username': 'username',
    'hash': '69a9871558fbbe4cd0dbaba52fa1cc4f38315d3245b7504381a64139fb024b5b'
}


def test_valid_token():
    assert api.check_token(VALID_TOKEN)


def test_invalid_token():
    with pytest.raises(exceptions.ValidationError):
        api.check_token(INVALID_TOKEN)


def test_widget():
    assert auth_widget.check_token(VALID_DATA, VALID_TOKEN)


def test_invalid_widget_data():
    assert not auth_widget.check_token(INVALID_DATA, VALID_TOKEN)
