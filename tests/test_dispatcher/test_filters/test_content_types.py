import pytest
from pydantic import ValidationError

from aiogram.dispatcher.filters import ContentTypesFilter


class TestContentTypesFilter:
    def test_validator_empty(self):
        filter_ = ContentTypesFilter()
        assert filter_.content_types == ["text"]

    def test_validator_empty_list(self):
        filter_ = ContentTypesFilter(content_types=[])
        assert filter_.content_types == ["text"]

    @pytest.mark.parametrize("values", [["text", "photo"], ["sticker"]])
    def test_validator_with_values(self, values):
        filter_ = ContentTypesFilter(content_types=values)
        assert filter_.content_types == values

    @pytest.mark.parametrize("values", [["test"], ["text", "test"], ["TEXT"]])
    def test_validator_with_bad_values(self, values):
        with pytest.raises(ValidationError):
            ContentTypesFilter(content_types=values)
