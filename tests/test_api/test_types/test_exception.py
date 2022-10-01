import pytest

from aiogram.exceptions import DetailedAiogramError


class TestException:
    @pytest.mark.parametrize(
        "message,result",
        [
            ["reason", "DetailedAiogramError('reason')"],
        ],
    )
    def test_representation(self, message: str, result: str):
        exc = DetailedAiogramError(message=message)
        assert repr(exc) == result
