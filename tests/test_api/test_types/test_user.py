import pytest

from tests.factories.user import UserFactory


class TestUser:
    @pytest.mark.parametrize(
        "first_name,last_name,result",
        [
            ["User", None, "User"],
            ["", None, ""],
            [" ", None, " "],
            ["User", "Name", "User Name"],
            ["User", " ", "User  "],
            [" ", " ", "   "],
        ],
    )
    def test_full_name(self, first_name: str, last_name: str, result: bool):
        user = UserFactory(first_name=first_name, last_name=last_name)
        assert user.full_name == result
