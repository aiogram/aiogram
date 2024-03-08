import pytest

from aiogram.utils.web_app import (
    WebAppInitData,
    check_webapp_signature,
    parse_webapp_init_data,
    safe_parse_webapp_init_data,
)


class TestWebApp:
    @pytest.mark.parametrize(
        "token,case,result",
        [
            [
                "42:TEST",
                "auth_date=1650385342"
                "&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D"
                "&query_id=test"
                "&hash=46d2ea5e32911ec8d30999b56247654460c0d20949b6277af519e76271182803",
                True,
            ],
            [
                "42:TEST",
                "auth_date=1650385342"
                "&user=%7B%22id%22%3A+%22123456789%22%2C+%22first_name%22%3A+%22PlaceholderFirstName%22%2C+%22last_name%22%3A+%22PlaceholderLastName+%5Cud83c%5Cuddfa%5Cud83c%5Cudde6%22%2C+%22username%22%3A+%22Latand%22%2C+%22language_code%22%3A+%22en%22%2C+%22is_premium%22%3A+%22true%22%2C+%22allows_write_to_pm%22%3A+%22true%22%7D"
                "&query_id=test"
                "&hash=b3c8b293f14ad0f7f0abcf769aea1209a72295d30a87eb0e74df855d32e53bfe",
                True,
            ],
            [
                "42:INVALID",
                "auth_date=1650385342"
                "&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D"
                "&query_id=test"
                "&hash=46d2ea5e32911ec8d30999b56247654460c0d20949b6277af519e76271182803",
                False,
            ],
            [
                "42:TEST",
                "user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D&query_id=test&hash=test",
                False,
            ],
            [
                "42:TEST",
                "user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D&query_id=test",
                False,
            ],
            ["42:TEST", "", False],
            ["42:TEST", "test&foo=bar=baz", False],
        ],
    )
    def test_check_webapp_signature(self, token, case, result):
        assert check_webapp_signature(token, case) is result

    def test_parse_web_app_init_data(self):
        parsed = parse_webapp_init_data(
            "auth_date=1650385342"
            "&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D"
            "&query_id=test"
            "&hash=46d2ea5e32911ec8d30999b56247654460c0d20949b6277af519e76271182803",
        )
        assert isinstance(parsed, WebAppInitData)
        assert parsed.user
        assert parsed.user.first_name == "Test"
        assert parsed.user.id == 42
        assert parsed.query_id == "test"
        assert parsed.hash == "46d2ea5e32911ec8d30999b56247654460c0d20949b6277af519e76271182803"
        assert parsed.auth_date.year == 2022

    def test_valid_safe_parse_webapp_init_data(self):
        assert safe_parse_webapp_init_data(
            "42:TEST",
            "auth_date=1650385342"
            "&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D"
            "&query_id=test"
            "&hash=46d2ea5e32911ec8d30999b56247654460c0d20949b6277af519e76271182803",
        )

    def test_invalid_safe_parse_webapp_init_data(self):
        with pytest.raises(ValueError):
            safe_parse_webapp_init_data(
                "42:TOKEN",
                "auth_date=1650385342"
                "&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D"
                "&query_id=test"
                "&hash=test",
            )
