"""Regression tests for issue #1925.

``RichTextUnion`` mixes ``str``, ``list[RichTextUnion]`` and the ``RichText*`` models,
so it cannot use ``Field(discriminator="type")`` like the unions fixed in #1842. As a
plain smart union Pydantic tried every member at every nesting level, which made
validating nested rich text (bold inside italic inside spoiler ...) exponential and
froze the event loop. It is now a callable-discriminated union: plain strings and
arrays are tagged by their Python type, models by their ``type`` field.
"""

import signal
import time

import pytest
from pydantic import TypeAdapter, ValidationError

from aiogram.types import (
    RichBlockDetails,
    RichBlockParagraph,
    RichTextBold,
    RichTextItalic,
    RichTextSpoiler,
    RichTextUnion,
    Update,
)

RICH_TEXT = TypeAdapter(RichTextUnion)
KINDS = ["spoiler", "bold", "subscript", "italic", "underline"]


def _nested_text(depth: int) -> dict | str:
    node: dict | str = "leaf"
    for index in reversed(range(depth)):
        node = {"type": KINDS[index % len(KINDS)], "text": node}
    return node


class TestRichTextUnionIsDiscriminated:
    def test_reported_update_resolves_to_concrete_types(self):
        update = Update.model_validate(
            {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "date": 1,
                    "chat": {"id": 1, "type": "private"},
                    "rich_message": {
                        "blocks": [
                            {
                                "type": "details",
                                "summary": "",
                                "blocks": [{"type": "paragraph", "text": _nested_text(5)}],
                            }
                        ]
                    },
                },
            }
        )

        details = update.message.rich_message.blocks[0]
        assert isinstance(details, RichBlockDetails)
        paragraph = details.blocks[0]
        assert isinstance(paragraph, RichBlockParagraph)
        node = paragraph.text
        for kind in KINDS:
            assert node.type == kind
            node = node.text
        assert node == "leaf"

    def test_mixed_list_and_str(self):
        value = RICH_TEXT.validate_python(
            ["plain", {"type": "bold", "text": ["a", {"type": "italic", "text": "b"}]}]
        )

        assert value[0] == "plain"
        assert isinstance(value[1], RichTextBold)
        assert value[1].text[0] == "a"
        assert isinstance(value[1].text[1], RichTextItalic)

    def test_tuple_input(self):
        assert RICH_TEXT.validate_python(("a", "b")) == ["a", "b"]

    def test_json_input(self):
        value = RICH_TEXT.validate_json('{"type": "spoiler", "text": ["a"]}')

        assert isinstance(value, RichTextSpoiler)
        assert value.text == ["a"]

    def test_model_instance_input(self):
        text = RichTextBold(text=RichTextItalic(text="x"))

        paragraph = RichBlockParagraph(text=text)

        assert paragraph.text is text
        assert isinstance(paragraph.text.text, RichTextItalic)

    def test_invalid_text_type_raises_discriminated_union_error(self):
        with pytest.raises(ValidationError) as exc_info:
            RichBlockParagraph.model_validate({"text": {"type": "definitely_not_text"}})

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "union_tag_invalid"
        assert errors[0]["loc"] == ("text",)


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="performance guard relies on SIGALRM (POSIX only)",
)
def test_nested_rich_text_validation_is_not_exponential():
    payload = _nested_text(30)

    def _abort(signum, frame):
        raise TimeoutError

    previous_handler = signal.signal(signal.SIGALRM, _abort)
    try:
        signal.setitimer(signal.ITIMER_REAL, 5.0)
        start = time.perf_counter()
        RICH_TEXT.validate_python(payload)
        elapsed = time.perf_counter() - start
    except TimeoutError:
        pytest.fail(
            "Validating a depth-30 nested RichText exceeded 5s -- "
            "RichTextUnion likely regressed to a non-discriminated (exponential) union."
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)

    assert elapsed < 1.0
