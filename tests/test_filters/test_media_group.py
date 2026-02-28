import datetime

import pytest

from aiogram.filters.media_group import DEFAULT_MAX_MEDIA_COUNT, MIN_MEDIA_COUNT, MediaGroupFilter
from aiogram.types import Chat, Message


class TestMediaGroupFilter:
    @pytest.mark.parametrize(
        "args,min_count,max_count",
        [
            ((), MIN_MEDIA_COUNT, DEFAULT_MAX_MEDIA_COUNT),
            ((3,), 3, 3),
            ((None, 3), 3, DEFAULT_MAX_MEDIA_COUNT),
            ((None, None, 3), MIN_MEDIA_COUNT, 3),
        ],
    )
    def test_init_range(self, args, min_count, max_count):
        filter = MediaGroupFilter(*args)
        assert filter.max_media_count == max_count
        assert filter.min_media_count == min_count

    @pytest.mark.parametrize(
        "count,min_count,max_count",
        [
            (1, None, 1),
            (1, 1, None),
            (None, 1, None),
            (None, None, 1),
            (1, None, None),
            (None, 5, 3),
        ],
    )
    def test_raise_error(self, count, min_count, max_count):
        with pytest.raises(ValueError):
            MediaGroupFilter(count, min_count, max_count)

    @pytest.mark.parametrize(
        "min_count,max_count,media_count,result",
        [
            [2, 2, 1, False],
            [2, 2, 2, True],
            [2, 2, 3, False],
            [2, 5, 2, True],
            [2, 5, 5, True],
            [2, 5, 6, False],
        ],
    )
    async def test_call(self, min_count, max_count, media_count, result):
        filter = MediaGroupFilter(min_media_count=min_count, max_media_count=max_count)
        album = [
            Message(
                message_id=i,
                date=datetime.datetime.now(),
                chat=Chat(id=42, type="private"),
            )
            for i in range(media_count)
        ]
        response = await filter(album[0], album)
        assert bool(response) is result
        if result:
            assert response.get("media_count") == media_count

    def test_str_count(self):
        filter = MediaGroupFilter(5)
        assert str(filter) == "MediaGroupFilter(count=5)"

    def test_str_range(self):
        filter = MediaGroupFilter(min_media_count=2, max_media_count=5)
        assert str(filter) == "MediaGroupFilter(min_media_count=2, max_media_count=5)"
