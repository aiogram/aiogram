import pytest

from aiogram.types import CallbackQuery
from aiogram.utils.callback_data import CallbackData


class TestCallbackData:
    @pytest.mark.asyncio
    async def test_cb(self):
        cb = CallbackData('simple', 'action')
        assert cb.new('x') == 'simple:x'
        assert cb.new(action='y') == 'simple:y'
        assert cb.new('') == 'simple:'

        assert (await cb.filter().check(CallbackQuery(data='simple:'))) == {'callback_data': {'@': 'simple', 'action': ''}}
        assert (await cb.filter().check(CallbackQuery(data='simple:x'))) == {'callback_data': {'@': 'simple', 'action': 'x'}}
        assert (await cb.filter(action='y').check(CallbackQuery(data='simple:x'))) is False

    @pytest.mark.asyncio
    async def test_cb_double(self):
        cb = CallbackData('double', 'pid', 'action')
        assert cb.new('123', 'x') == 'double:123:x'
        assert cb.new(pid=456, action='y') == 'double:456:y'
        assert cb.new('', 'z') == 'double::z'
        assert cb.new('789', '') == 'double:789:'

        assert (await cb.filter().check(CallbackQuery(data='double::'))) == {'callback_data': {'@': 'double', 'pid': '', 'action': ''}}
        assert (await cb.filter().check(CallbackQuery(data='double:x:'))) == {'callback_data': {'@': 'double', 'pid': 'x', 'action': ''}}
        assert (await cb.filter().check(CallbackQuery(data='double::y'))) == {'callback_data': {'@': 'double', 'pid': '', 'action': 'y'}}
        assert (await cb.filter(action='x').check(CallbackQuery(data='double:123:x'))) == {'callback_data': {'@': 'double', 'pid': '123', 'action': 'x'}}

    @pytest.mark.asyncio
    async def test_cb_zero(self):
        cb = CallbackData('zero')
        assert cb.new() == 'zero'

        assert (await cb.filter().check(CallbackQuery(data='zero'))) == {'callback_data': {'@': 'zero'}}
        assert (await cb.filter().check(CallbackQuery(data='zero:'))) is False
        assert (await cb.filter().check(CallbackQuery(data='bla'))) is False
