import pytest

from aiogram.utils.web_app import WebAppInitData
from aiogram.utils.web_app_signature import (
    check_webapp_signature,
    safe_check_webapp_init_data_from_signature,
)

PRIVATE_KEY = bytes.fromhex("c80e09dc60f5efcf2e1f8d0793358e0ea3371267bef0024588f7bf67cf48dfb9")
PUBLIC_KEY = bytes.fromhex("4112765021341e5415e772cd65903f6b94e3ea1c2ab669e6d3e18ee2db00da61")


class TestWebAppSignature:
    @pytest.mark.parametrize(
        "bot_id,case,result",
        [
            [
                42,
                "auth_date=1650385342&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D&query_id=test&signature=JQ0JR2tjC65yq_jNZV0wuJVX6J-SWPMV0mprUXG34g-NvxL4RcF1Rz5n4VVo00VRghEUBf5t___uoeb1-jU_Cw",
                True,
            ],
            [
                42,
                "auth_date=1650385342&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D&query_id=test&signature=JQ0JR2tjC65yq_jNZV0wuJVX6J-SWPMV0mprUXG34g-NvxL4RcF1Rz5n4VVo00VRghEUBf5t___uoeb1-j1U_w",
                False,
            ],
            [
                42,
                "auth_date=1650385342&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D&query_id=test",
                False,
            ],
            [
                42,
                "",
                False,
            ],
            [42, "test&foo=bar=baz", False],
        ],
    )
    def test_check_webapp_signature(self, bot_id: int, case: str, result: bool):
        assert check_webapp_signature(bot_id, case, PUBLIC_KEY) is result

    def test_safe_check_webapp_init_data_from_signature(self):
        result = safe_check_webapp_init_data_from_signature(
            42,
            "auth_date=1650385342&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D&query_id=test&hash=123&signature=JQ0JR2tjC65yq_jNZV0wuJVX6J-SWPMV0mprUXG34g-NvxL4RcF1Rz5n4VVo00VRghEUBf5t___uoeb1-jU_Cw",
            PUBLIC_KEY,
        )
        assert isinstance(result, WebAppInitData)
        assert result.user is not None
        assert result.user.id == 42
        assert result.user.first_name == "Test"
        assert result.query_id == "test"
        assert result.auth_date.year == 2022
        assert result.hash == "123"

    def test_safe_check_webapp_init_data_from_signature_invalid(self):
        with pytest.raises(ValueError):
            safe_check_webapp_init_data_from_signature(
                42,
                "auth_date=1650385342&user=%7B%22id%22%3A42%2C%22first_name%22%3A%22Test%22%7D&query_id=test&hash=123&signature=JQ0JR2tjC65yq_jNZV0wuJVX6J-SWPMV0mprUXG34g-NvxL4RcF1Rz5n4VVo00VRghEUBf5t___uoeb1-j1U_w",
                PUBLIC_KEY,
            )