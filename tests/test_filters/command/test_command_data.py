import pytest

from aiogram.filters.command.data.base import DeeplinkData, DeeplinkDataException
from aiogram.filters.command.data.codecs import PositionalCodec


class MyOrder(DeeplinkData, prefix="order", codec=PositionalCodec(sep="_")):
    order_id: int
    promo: str | None = None


class PackNoPfx(DeeplinkData):
    val: str


class PackWithSpace(DeeplinkData, prefix="s"):
    val: str


class PackTooLong(DeeplinkData, prefix="p", codec=PositionalCodec(sep="_")):
    val: str


class TestDeeplinkData:
    def test_pack(self):
        assert MyOrder(order_id=42).pack() == "order42"
        assert MyOrder(order_id=7, promo="SALE").pack() == "order7_SALE"

    @pytest.mark.parametrize("model,match", [
        (PackNoPfx(val="x"),        "prefix is required"),
        (PackWithSpace(val="a b"),  "not allowed"),
        (PackTooLong(val="x" * 64), "too long"),
    ])
    def test_pack_raises(self, model, match):
        with pytest.raises(DeeplinkDataException, match=match):
            model.pack()

    def test_unpack(self):
        assert MyOrder.unpack("order42") == MyOrder(order_id=42)
        assert MyOrder.unpack("order7_SALE") == MyOrder(order_id=7, promo="SALE")

    def test_unpack_bad_prefix_raises(self):
        with pytest.raises(DeeplinkDataException, match="Bad prefix"):
            MyOrder.unpack("wrong42")

    def test_unpack_optional(self):
        class MyCmd(DeeplinkData, prefix="x", codec=PositionalCodec(sep="_")):
            val: str
            tag: str | None = None

        assert MyCmd.unpack("xhello") == MyCmd(val="hello")
        assert MyCmd.unpack("xhello_sale") == MyCmd(val="hello", tag="sale")

        class AllOpt(DeeplinkData, prefix="p", codec=PositionalCodec(sep="_")):
            val: str | None = None

        assert AllOpt.unpack("p") == AllOpt(val=None)

    def test_unpack_optional_without_default(self):
        class MyData(DeeplinkData, prefix="x", codec=PositionalCodec(sep="_")):
            id: int
            extra: int | None

        assert MyData.unpack("x1") == MyData(id=1, extra=None)

    def test_encoded_roundtrip(self):
        class MyB64(DeeplinkData, prefix="b", encoded=True):
            text: str
            num: int = 0

        model = MyB64(text="hello world", num=7)
        assert MyB64.unpack(model.pack()) == model
