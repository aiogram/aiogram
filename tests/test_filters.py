import re
from typing import Match

import pytest

from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.types import Message, CallbackQuery, InlineQuery, Poll

# enable asyncio mode
pytestmark = pytest.mark.asyncio


def data_sample_1():
    return [
        ('', ''),
        ('', 'exAmple_string'),

        ('example_string', 'example_string'),
        ('example_string', 'exAmple_string'),
        ('exAmple_string', 'example_string'),

        ('example_string', 'example_string_dsf'),
        ('example_string', 'example_striNG_dsf'),
        ('example_striNG', 'example_string_dsf'),

        ('example_string', 'not_example_string'),
        ('example_string', 'not_eXample_string'),
        ('EXample_string', 'not_example_string'),
    ]


class TestTextFilter:

    @staticmethod
    async def _run_check(check, test_text):
        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_prefix, test_text", data_sample_1())
    async def test_startswith(self, test_prefix, test_text, ignore_case):
        test_filter = Text(startswith=test_prefix, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_prefix = test_prefix.lower()
                _test_text = test_text.lower()
            else:
                _test_prefix = test_prefix
                _test_text = test_text

            return result is _test_text.startswith(_test_prefix)

        await self._run_check(check, test_text)

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_prefix_list, test_text", [
        (['not_example', ''], ''),
        (['', 'not_example'], 'exAmple_string'),

        (['not_example', 'example_string'], 'example_string'),
        (['example_string', 'not_example'], 'exAmple_string'),
        (['not_example', 'exAmple_string'], 'example_string'),

        (['not_example', 'example_string'], 'example_string_dsf'),
        (['example_string', 'not_example'], 'example_striNG_dsf'),
        (['not_example', 'example_striNG'], 'example_string_dsf'),

        (['not_example', 'example_string'], 'not_example_string'),
        (['example_string', 'not_example'], 'not_eXample_string'),
        (['not_example', 'EXample_string'], 'not_example_string'),
    ])
    async def test_startswith_list(self, test_prefix_list, test_text, ignore_case):
        test_filter = Text(startswith=test_prefix_list, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_prefix_list = map(str.lower, test_prefix_list)
                _test_text = test_text.lower()
            else:
                _test_prefix_list = test_prefix_list
                _test_text = test_text

            return result is any(map(_test_text.startswith, _test_prefix_list))

        await self._run_check(check, test_text)

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_postfix, test_text", data_sample_1())
    async def test_endswith(self, test_postfix, test_text, ignore_case):
        test_filter = Text(endswith=test_postfix, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_postfix = test_postfix.lower()
                _test_text = test_text.lower()
            else:
                _test_postfix = test_postfix
                _test_text = test_text

            return result is _test_text.endswith(_test_postfix)

        await self._run_check(check, test_text)

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_postfix_list, test_text", [
        (['', 'not_example'], ''),
        (['not_example', ''], 'exAmple_string'),

        (['example_string', 'not_example'], 'example_string'),
        (['not_example', 'example_string'], 'exAmple_string'),
        (['exAmple_string', 'not_example'], 'example_string'),

        (['not_example', 'example_string'], 'example_string_dsf'),
        (['example_string', 'not_example'], 'example_striNG_dsf'),
        (['not_example', 'example_striNG'], 'example_string_dsf'),

        (['not_example', 'example_string'], 'not_example_string'),
        (['example_string', 'not_example'], 'not_eXample_string'),
        (['not_example', 'EXample_string'], 'not_example_string'),
    ])
    async def test_endswith_list(self, test_postfix_list, test_text, ignore_case):
        test_filter = Text(endswith=test_postfix_list, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_postfix_list = map(str.lower, test_postfix_list)
                _test_text = test_text.lower()
            else:
                _test_postfix_list = test_postfix_list
                _test_text = test_text

            return result is any(map(_test_text.endswith, _test_postfix_list))

        await self._run_check(check, test_text)

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_string, test_text", [
        ('', ''),
        ('', 'exAmple_string'),

        ('example_string', 'example_string'),
        ('example_string', 'exAmple_string'),
        ('exAmple_string', 'example_string'),

        ('example_string', 'example_string_dsf'),
        ('example_string', 'example_striNG_dsf'),
        ('example_striNG', 'example_string_dsf'),

        ('example_string', 'not_example_strin'),
        ('example_string', 'not_eXample_strin'),
        ('EXample_string', 'not_example_strin'),
    ])
    async def test_contains(self, test_string, test_text, ignore_case):
        test_filter = Text(contains=test_string, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_string = test_string.lower()
                _test_text = test_text.lower()
            else:
                _test_string = test_string
                _test_text = test_text

            return result is (_test_string in _test_text)

        await self._run_check(check, test_text)

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_filter_list, test_text", [
        (['a', 'ab', 'abc'], 'A'),
        (['a', 'ab', 'abc'], 'ab'),
        (['a', 'ab', 'abc'], 'aBc'),
        (['a', 'ab', 'abc'], 'd'),
    ])
    async def test_contains_list(self, test_filter_list, test_text, ignore_case):
        test_filter = Text(contains=test_filter_list, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_filter_list = list(map(str.lower, test_filter_list))
                _test_text = test_text.lower()
            else:
                _test_filter_list = test_filter_list
                _test_text = test_text

            return result is all(map(_test_text.__contains__, _test_filter_list))

        await self._run_check(check, test_text)

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_filter_text, test_text", [
        ('', ''),
        ('', 'exAmple_string'),

        ('example_string', 'example_string'),
        ('example_string', 'exAmple_string'),
        ('exAmple_string', 'example_string'),

        ('example_string', 'not_example_string'),
        ('example_string', 'not_eXample_string'),
        ('EXample_string', 'not_example_string'),
    ])
    async def test_equals_string(self, test_filter_text, test_text, ignore_case):
        test_filter = Text(equals=test_filter_text, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_filter_text = test_filter_text.lower()
                _test_text = test_text.lower()
            else:
                _test_filter_text = test_filter_text
                _test_text = test_text
            return result is (_test_text == _test_filter_text)

        await self._run_check(check, test_text)

    @pytest.mark.parametrize('ignore_case', (True, False))
    @pytest.mark.parametrize("test_filter_list, test_text", [
        (['new_string', ''], ''),
        (['', 'new_string'], 'exAmple_string'),

        (['example_string'], 'example_string'),
        (['example_string'], 'exAmple_string'),
        (['exAmple_string'], 'example_string'),

        (['example_string'], 'not_example_string'),
        (['example_string'], 'not_eXample_string'),
        (['EXample_string'], 'not_example_string'),

        (['example_string', 'new_string'], 'example_string'),
        (['new_string', 'example_string'], 'exAmple_string'),
        (['exAmple_string', 'new_string'], 'example_string'),

        (['example_string', 'new_string'], 'not_example_string'),
        (['new_string', 'example_string'], 'not_eXample_string'),
        (['EXample_string', 'new_string'], 'not_example_string'),
    ])
    async def test_equals_list(self, test_filter_list, test_text, ignore_case):
        test_filter = Text(equals=test_filter_list, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_filter_list = list(map(str.lower, test_filter_list))
                _test_text = test_text.lower()
            else:
                _test_filter_list = test_filter_list
                _test_text = test_text
            assert result is (_test_text in _test_filter_list)

        await check(Message(text=test_text))
        await check(CallbackQuery(data=test_text))
        await check(InlineQuery(query=test_text))
        await check(Poll(question=test_text))


class TestCommandStart:
    START = '/start'
    GOOD = 'foo'
    BAD = 'bar'
    GOOD_PATTERN = re.compile(r'^f..$')
    BAD_PATTERN = re.compile(r'^b..$')
    ENCODED = 'Zm9v'

    async def test_start_command_without_payload(self):
        test_filter = CommandStart()  # empty filter
        message = Message(text=self.START)
        result = await test_filter.check(message)
        assert result

    async def test_start_command_payload_is_matched(self):
        test_filter = CommandStart(deep_link=self.GOOD)
        message = Message(text=f'{self.START} {self.GOOD}')
        result = await test_filter.check(message)
        assert result == {'deep_link': self.GOOD}

    async def test_start_command_payload_is_not_matched(self):
        test_filter = CommandStart(deep_link=self.GOOD)
        message = Message(text=f'{self.START} {self.BAD}')
        result = await test_filter.check(message)
        assert result is False

    async def test_start_command_payload_pattern_is_matched(self):
        test_filter = CommandStart(deep_link=self.GOOD_PATTERN)
        message = Message(text=f'{self.START} {self.GOOD}')
        result = await test_filter.check(message)
        assert isinstance(result, dict)
        match = result.get('deep_link')
        assert isinstance(match, Match)

    async def test_start_command_payload_pattern_is_not_matched(self):
        test_filter = CommandStart(deep_link=self.BAD_PATTERN)
        message = Message(text=f'{self.START} {self.GOOD}')
        result = await test_filter.check(message)
        assert result is False

    async def test_start_command_payload_is_encoded(self):
        test_filter = CommandStart(deep_link=self.GOOD, encoded=True)
        message = Message(text=f'{self.START} {self.ENCODED}')
        result = await test_filter.check(message)
        assert result == {'deep_link': self.GOOD}
