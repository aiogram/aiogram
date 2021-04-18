from dataclasses import dataclass
from typing import cast

import pytest
from pydantic import ValidationError

from aiogram.dispatcher.filters import ContentTypesFilter
from aiogram.types import ContentType, Message


@dataclass
class MinimalMessage:
    content_type: str


class TestContentTypesFilter:
    @pytest.mark.asyncio
    async def test_validator_empty(self):
        filter_ = ContentTypesFilter()
        assert not filter_.content_types
        await filter_(cast(Message, MinimalMessage(ContentType.TEXT)))
        assert filter_.content_types == [ContentType.TEXT]

    def test_validator_empty_list(self):
        filter_ = ContentTypesFilter(content_types=[])
        assert filter_.content_types == []

    def test_convert_to_list(self):
        filter_ = ContentTypesFilter(content_types="text")
        assert filter_.content_types
        assert isinstance(filter_.content_types, list)
        assert filter_.content_types[0] == "text"
        assert filter_ == ContentTypesFilter(content_types=["text"])

    @pytest.mark.parametrize("values", [["text", "photo"], ["sticker"]])
    def test_validator_with_values(self, values):
        filter_ = ContentTypesFilter(content_types=values)
        assert filter_.content_types == values

    @pytest.mark.parametrize("values", [["test"], ["text", "test"], ["TEXT"]])
    def test_validator_with_bad_values(self, values):
        with pytest.raises(ValidationError):
            ContentTypesFilter(content_types=values)

    @pytest.mark.parametrize(
        "values,content_type,result",
        [
            [[], ContentType.TEXT, True],
            [[ContentType.TEXT], ContentType.TEXT, True],
            [[ContentType.PHOTO], ContentType.TEXT, False],
            [[ContentType.ANY], ContentType.TEXT, True],
            [[ContentType.TEXT, ContentType.PHOTO, ContentType.DOCUMENT], ContentType.TEXT, True],
            [[ContentType.ANY, ContentType.PHOTO, ContentType.DOCUMENT], ContentType.TEXT, True],
        ],
    )
    @pytest.mark.asyncio
    async def test_call(self, values, content_type, result):
        filter_ = ContentTypesFilter(content_types=values)
        assert await filter_(cast(Message, MinimalMessage(content_type=content_type))) == result
