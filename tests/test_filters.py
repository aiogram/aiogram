import pytest

from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery, InlineQuery, Poll


class TestTextFilter:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_prefix, test_text, ignore_case",
                             [('', '', True),
                              ('', 'exAmple_string', True),
                              ('', '', False),
                              ('', 'exAmple_string', False),

                              ('example_string', 'example_string', True),
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
    @pytest.mark.parametrize("test_prefix_list, test_text, ignore_case",
                             [(['not_example', ''], '', True),
                              (['', 'not_example'], 'exAmple_string', True),
                              (['not_example', ''], '', False),
                              (['', 'not_example'], 'exAmple_string', False),

                              (['example_string', 'not_example'], 'example_string', True),
                              (['not_example', 'example_string'], 'exAmple_string', True),
                              (['exAmple_string', 'not_example'], 'example_string', True),

                              (['not_example', 'example_string'], 'example_string', False),
                              (['example_string', 'not_example'], 'exAmple_string', False),
                              (['not_example', 'exAmple_string'], 'example_string', False),

                              (['example_string', 'not_example'], 'example_string_dsf', True),
                              (['not_example', 'example_string'], 'example_striNG_dsf', True),
                              (['example_striNG', 'not_example'], 'example_string_dsf', True),

                              (['not_example', 'example_string'], 'example_string_dsf', False),
                              (['example_string', 'not_example'], 'example_striNG_dsf', False),
                              (['not_example', 'example_striNG'], 'example_string_dsf', False),

                              (['example_string', 'not_example'], 'not_example_string', True),
                              (['not_example', 'example_string'], 'not_eXample_string', True),
                              (['EXample_string', 'not_example'], 'not_example_string', True),

                              (['not_example', 'example_string'], 'not_example_string', False),
                              (['example_string', 'not_example'], 'not_eXample_string', False),
                              (['not_example', 'EXample_string'], 'not_example_string', False),
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

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_postfix, test_text, ignore_case",
                             [('', '', True),
                              ('', 'exAmple_string', True),
                              ('', '', False),
                              ('', 'exAmple_string', False),

                              ('example_string', 'example_string', True),
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
    @pytest.mark.parametrize("test_postfix_list, test_text, ignore_case",
                             [(['', 'not_example'], '', True),
                              (['not_example', ''], 'exAmple_string', True),
                              (['', 'not_example'], '', False),
                              (['not_example', ''], 'exAmple_string', False),

                              (['example_string', 'not_example'], 'example_string', True),
                              (['not_example', 'example_string'], 'exAmple_string', True),
                              (['exAmple_string', 'not_example'], 'example_string', True),

                              (['example_string', 'not_example'], 'example_string', False),
                              (['not_example', 'example_string'], 'exAmple_string', False),
                              (['exAmple_string', 'not_example'], 'example_string', False),

                              (['example_string', 'not_example'], 'example_string_dsf', True),
                              (['not_example', 'example_string'], 'example_striNG_dsf', True),
                              (['example_striNG', 'not_example'], 'example_string_dsf', True),

                              (['not_example', 'example_string'], 'example_string_dsf', False),
                              (['example_string', 'not_example'], 'example_striNG_dsf', False),
                              (['not_example', 'example_striNG'], 'example_string_dsf', False),

                              (['not_example', 'example_string'], 'not_example_string', True),
                              (['example_string', 'not_example'], 'not_eXample_string', True),
                              (['not_example', 'EXample_string'], 'not_eXample_string', True),

                              (['not_example', 'example_string'], 'not_example_string', False),
                              (['example_string', 'not_example'], 'not_eXample_string', False),
                              (['not_example', 'EXample_string'], 'not_example_string', False),
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
        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_string, test_text, ignore_case",
                             [('', '', True),
                              ('', 'exAmple_string', True),
                              ('', '', False),
                              ('', 'exAmple_string', False),

                              ('example_string', 'example_string', True),
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

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_filter_list, test_text, ignore_case",
                             [(['a', 'ab', 'abc'], 'A', True),
                              (['a', 'ab', 'abc'], 'ab', True),
                              (['a', 'ab', 'abc'], 'aBc', True),
                              (['a', 'ab', 'abc'], 'd', True),

                              (['a', 'ab', 'abc'], 'A', False),
                              (['a', 'ab', 'abc'], 'ab', False),
                              (['a', 'ab', 'abc'], 'aBc', False),
                              (['a', 'ab', 'abc'], 'd', False),
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

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_filter_text, test_text, ignore_case",
                             [('', '', True),
                              ('', 'exAmple_string', True),
                              ('', '', False),
                              ('', 'exAmple_string', False),

                              ('example_string', 'example_string', True),
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

        assert await check(Message(text=test_text))
        assert await check(CallbackQuery(data=test_text))
        assert await check(InlineQuery(query=test_text))
        assert await check(Poll(question=test_text))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_filter_list, test_text, ignore_case",
                             [(['', 'new_string'], '', True),
                              (['new_string', ''], 'exAmple_string', True),
                              (['new_string', ''], '', False),
                              (['', 'new_string'], 'exAmple_string', False),

                              (['example_string'], 'example_string', True),
                              (['example_string'], 'exAmple_string', True),
                              (['exAmple_string'], 'example_string', True),

                              (['example_string'], 'example_string', False),
                              (['example_string'], 'exAmple_string', False),
                              (['exAmple_string'], 'example_string', False),

                              (['example_string'], 'not_example_string', True),
                              (['example_string'], 'not_eXample_string', True),
                              (['EXample_string'], 'not_eXample_string', True),

                              (['example_string'], 'not_example_string', False),
                              (['example_string'], 'not_eXample_string', False),
                              (['EXample_string'], 'not_example_string', False),

                              (['example_string', 'new_string'], 'example_string', True),
                              (['new_string', 'example_string'], 'exAmple_string', True),
                              (['exAmple_string', 'new_string'], 'example_string', True),

                              (['example_string', 'new_string'], 'example_string', False),
                              (['new_string', 'example_string'], 'exAmple_string', False),
                              (['exAmple_string', 'new_string'], 'example_string', False),

                              (['example_string', 'new_string'], 'not_example_string', True),
                              (['new_string', 'example_string'], 'not_eXample_string', True),
                              (['EXample_string', 'new_string'], 'not_eXample_string', True),

                              (['example_string', 'new_string'], 'not_example_string', False),
                              (['new_string', 'example_string'], 'not_eXample_string', False),
                              (['EXample_string', 'new_string'], 'not_example_string', False),
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
