import pytest

from aiogram.utils.auth_widget import check_integrity

TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


@pytest.fixture
def data():
    return {
        "id": "42",
        "first_name": "John",
        "last_name": "Smith",
        "username": "username",
        "photo_url": "https://t.me/i/userpic/320/picname.jpg",
        "auth_date": "1565810688",
        "hash": "c303db2b5a06fe41d23a9b14f7c545cfc11dcc7473c07c9c5034ae60062461ce",
    }


class TestCheckIntegrity:
    def test_ok(self, data):
        assert check_integrity(TOKEN, data) is True

    def test_fail(self, data):
        data.pop("username")
        assert check_integrity(TOKEN, data) is False


class TestCheckIntegrityInvalidHash:
    @pytest.mark.parametrize(
        "hash_value",
        [
            pytest.param("é" * 64, id="latin-1-accent"),
            pytest.param("日本語", id="cjk"),
            pytest.param("🙂" * 32, id="emoji"),
            pytest.param("0" * 63 + "é", id="ascii-prefix-then-non-ascii"),
        ],
    )
    def test_non_ascii_hash_returns_false(self, data, hash_value):
        """A non-ASCII hash is invalid input and must be rejected, not raise.

        hmac.compare_digest refuses non-ASCII str operands. Since `hash` comes
        straight from the client-supplied Login Widget data, a caller relying
        on the `-> bool` contract would otherwise surface an unhandled
        TypeError on hostile input.
        """
        data["hash"] = hash_value
        assert check_integrity(TOKEN, data) is False

    def test_empty_hash_returns_false(self, data):
        data["hash"] = ""
        assert check_integrity(TOKEN, data) is False
