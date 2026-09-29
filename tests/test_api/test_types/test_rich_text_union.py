import pytest
from pydantic import ValidationError

from aiogram.types import RichMessage
from aiogram.types.rich_text_bold import RichTextBold
from aiogram.types.rich_text_italic import RichTextItalic
from aiogram.types.rich_text_spoiler import RichTextSpoiler
from aiogram.types.rich_text_subscript import RichTextSubscript
from aiogram.types.rich_text_underline import RichTextUnderline


def _nested_text(depth: int):
    chain = ["spoiler", "subscript", "bold", "italic", "underline"]
    node = "deep"
    for index in range(depth):
        node = {"type": chain[index % len(chain)], "text": node}
    return node


class TestRichTextUnion:
    def test_deeply_nested_text_resolves_each_level(self):
        # Regression test for https://github.com/aiogram/aiogram/issues/1925:
        # nested rich text used to hang validation (untagged union re-tried
        # every member at every nesting level), it must resolve in linear time.
        message = RichMessage.model_validate(
            {"blocks": [{"type": "paragraph", "text": _nested_text(8)}]},
        )

        # depth 8 wraps as bold -> subscript -> spoiler -> underline
        # -> italic -> bold -> subscript -> spoiler -> "deep"
        text = message.blocks[0].text
        assert isinstance(text, RichTextBold)
        assert isinstance(text.text, RichTextSubscript)
        assert isinstance(text.text.text, RichTextSpoiler)
        assert isinstance(text.text.text.text, RichTextUnderline)
        assert isinstance(text.text.text.text.text, RichTextItalic)
        assert text.text.text.text.text.text.text.text.text == "deep"

    def test_many_nested_blocks(self):
        message = RichMessage.model_validate(
            {
                "blocks": [{"type": "paragraph", "text": _nested_text(4)} for _ in range(40)],
            },
        )
        assert len(message.blocks) == 40
        assert isinstance(message.blocks[0].text, RichTextItalic)

    @pytest.mark.parametrize(
        "value,expected_type",
        [
            ("plain", str),
            (["a", {"type": "bold", "text": "b"}], list),
            ({"type": "bold", "text": "b"}, RichTextBold),
        ],
    )
    def test_scalar_list_and_model_members(self, value, expected_type):
        message = RichMessage.model_validate(
            {"blocks": [{"type": "paragraph", "text": value}]},
        )
        assert isinstance(message.blocks[0].text, expected_type)

    def test_serialization_round_trip(self):
        message = RichMessage.model_validate(
            {"blocks": [{"type": "paragraph", "text": _nested_text(6)}]},
        )
        assert RichMessage.model_validate(message.model_dump()) == message

    def test_unknown_type_is_rejected(self):
        with pytest.raises(ValidationError):
            RichMessage.model_validate(
                {"blocks": [{"type": "paragraph", "text": {"type": "nope", "text": "x"}}]},
            )
