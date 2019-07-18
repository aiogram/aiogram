import pytest

from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery, InlineQuery, Poll


class TestTextFilter:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_prefix, test_text, ignore_case",
                             [('example_string', 'example_string', True),
                              ('example_string', 'exAmple_string', True),
                              ('exAmple_string', 'example_string', True),

                              ('example_string', 'example_string', False),
                              ('example_string', 'exAmple_string', False),
                              ('exAmple_string', 'example_string', False),

                              ('example_string', 'example_string_dsf', True),
                              ('example_string', 'example_striNG_dsf', True),
                              ('example_striNG', 'example_string_dsf', True),

                              ('example_string', 'example_string_dsf', False),
                              ('example_string', 'example_striNG_dsf', False),
                              ('example_striNG', 'example_string_dsf', False),

                              ('example_string', 'not_example_string', True),
                              ('example_string', 'not_eXample_string', True),
                              ('EXample_string', 'not_example_string', True),

                              ('example_string', 'not_example_string', False),
                              ('example_string', 'not_eXample_string', False),
                              ('EXample_string', 'not_example_string', False),
                              ])
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

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_postfix, test_text, ignore_case",
                             [('example_string', 'example_string', True),
                              ('example_string', 'exAmple_string', True),
                              ('exAmple_string', 'example_string', True),

                              ('example_string', 'example_string', False),
                              ('example_string', 'exAmple_string', False),
                              ('exAmple_string', 'example_string', False),

                              ('example_string', 'example_string_dsf', True),
                              ('example_string', 'example_striNG_dsf', True),
                              ('example_striNG', 'example_string_dsf', True),

                              ('example_string', 'example_string_dsf', False),
                              ('example_string', 'example_striNG_dsf', False),
                              ('example_striNG', 'example_string_dsf', False),

                              ('example_string', 'not_example_string', True),
                              ('example_string', 'not_eXample_string', True),
                              ('EXample_string', 'not_eXample_string', True),

                              ('example_string', 'not_example_string', False),
                              ('example_string', 'not_eXample_string', False),
                              ('EXample_string', 'not_example_string', False),
                              ])
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

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_string, test_text, ignore_case",
                             [('example_string', 'example_string', True),
                              ('example_string', 'exAmple_string', True),
                              ('exAmple_string', 'example_string', True),

                              ('example_string', 'example_string', False),
                              ('example_string', 'exAmple_string', False),
                              ('exAmple_string', 'example_string', False),

                              ('example_string', 'example_string_dsf', True),
                              ('example_string', 'example_striNG_dsf', True),
                              ('example_striNG', 'example_string_dsf', True),

                              ('example_string', 'example_string_dsf', False),
                              ('example_string', 'example_striNG_dsf', False),
                              ('example_striNG', 'example_string_dsf', False),

                              ('example_string', 'not_example_strin', True),
                              ('example_string', 'not_eXample_strin', True),
                              ('EXample_string', 'not_eXample_strin', True),

                              ('example_string', 'not_example_strin', False),
                              ('example_string', 'not_eXample_strin', False),
                              ('EXample_string', 'not_example_strin', False),
                              ])
    async def test_contains(self, test_string, test_text, ignore_case):
        test_filter = Text(endswith=test_string, ignore_case=ignore_case)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_string = test_string.lower()
                _test_text = test_text.lower()
            else:
                _test_string = test_string
                _test_text = test_text

            return result is (_test_string in _test_text)

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_filter_text, test_text, ignore_case",
                             [('example_string', 'example_string', True),
                              ('example_string', 'exAmple_string', True),
                              ('exAmple_string', 'example_string', True),

                              ('example_string', 'example_string', False),
                              ('example_string', 'exAmple_string', False),
                              ('exAmple_string', 'example_string', False),

                              ('example_string', 'not_example_string', True),
                              ('example_string', 'not_eXample_string', True),
                              ('EXample_string', 'not_eXample_string', True),

                              ('example_string', 'not_example_string', False),
                              ('example_string', 'not_eXample_string', False),
                              ('EXample_string', 'not_example_string', False),
                              ])
    async def test_equals_string(self, test_filter_text, test_text, ignore_case):
        test_filter = Text(equals=test_filter_text)

        async def check(obj):
            result = await test_filter.check(obj)
            if ignore_case:
                _test_filter_text = test_filter_text.lower()
                _test_text = test_text.lower()
            else:
                _test_filter_text = test_filter_text
                _test_text = test_text
            return result is (_test_text == _test_filter_text)

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))
