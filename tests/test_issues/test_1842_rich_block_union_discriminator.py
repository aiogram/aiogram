"""Regression tests for issue #1842.

Subtype unions whose members share a unique constant tag field (``type`` /
``status`` / ``source``) are generated as Pydantic *discriminated* unions. This
keeps validation linear: Pydantic jumps straight to the matching member instead
of trying every option with smart-union backtracking, which is exponential for
nested structures such as ``RichBlockUnion`` (``blockquote`` inside
``blockquote`` ...) and its input-side mirror ``InputRichBlockUnion``.

These tests guard two things against future Pydantic updates:

* the discrimination is actually in effect (deterministic, timing-independent);
* deeply nested validation stays fast (does not regress to exponential).
"""

import signal
import time

import pytest
from pydantic import ValidationError

from aiogram.methods import AnswerWebAppQuery, EditMessageMedia
from aiogram.types import (
    InputMediaPhoto,
    InputRichBlockBlockQuotation,
    InputRichBlockParagraph,
    InputRichMessage,
    RichBlockBlockQuotation,
    RichBlockParagraph,
    RichMessage,
)


def _nested_blockquote(depth: int) -> dict:
    """Build ``depth`` nested ``blockquote`` blocks with a paragraph at the leaf.

    The input-side blocks use the same ``type`` tags and field names as the
    output-side ones, so the same payload validates against both unions.
    """
    node: dict = {"type": "blockquote", "blocks": [{"type": "paragraph", "text": "leaf"}]}
    for _ in range(depth):
        node = {"type": "blockquote", "blocks": [node]}
    return node


class TestRichBlockUnionIsDiscriminated:
    def test_invalid_block_type_raises_discriminated_union_error(self):
        # A discriminated union reports a single ``union_tag_invalid`` error at
        # the block location. A non-discriminated (smart) union would instead
        # emit one error per member, with much deeper/locations -- so this both
        # proves discrimination is in effect and pins the user-facing error.
        with pytest.raises(ValidationError) as exc_info:
            RichMessage.model_validate({"blocks": [{"type": "definitely_not_a_block"}]})

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "union_tag_invalid"
        assert errors[0]["loc"] == ("blocks", 0)

    def test_nested_blocks_resolve_to_concrete_types(self):
        message = RichMessage.model_validate({"blocks": [_nested_blockquote(depth=4)]})

        node = message.blocks[0]
        for _ in range(5):  # 1 outer + 4 nested blockquotes
            assert isinstance(node, RichBlockBlockQuotation)
            node = node.blocks[0]
        assert isinstance(node, RichBlockParagraph)
        assert node.text == "leaf"


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="performance guard relies on SIGALRM (POSIX only)",
)
def test_nested_rich_block_validation_is_not_exponential():
    # Correct (discriminated) validation is effectively instant even very deep.
    # If this regresses to smart-union backtracking, depth 30 is ~4**30 attempts
    # and would not finish, so the alarm aborts and fails the test instead of
    # hanging the suite.
    payload = {"blocks": [_nested_blockquote(depth=30)]}

    def _abort(signum, frame):
        raise TimeoutError

    previous_handler = signal.signal(signal.SIGALRM, _abort)
    try:
        signal.setitimer(signal.ITIMER_REAL, 5.0)
        start = time.perf_counter()
        RichMessage.model_validate(payload)
        elapsed = time.perf_counter() - start
    except TimeoutError:
        pytest.fail(
            "Validating a depth-30 nested RichBlock exceeded 5s -- "
            "RichBlockUnion likely regressed to a non-discriminated (exponential) union."
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)

    assert elapsed < 1.0


class TestInputRichBlockUnionIsDiscriminated:
    def test_invalid_block_type_raises_discriminated_union_error(self):
        with pytest.raises(ValidationError) as exc_info:
            InputRichMessage.model_validate({"blocks": [{"type": "definitely_not_a_block"}]})

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "union_tag_invalid"
        assert errors[0]["loc"] == ("blocks", 0)

    def test_nested_blocks_resolve_to_concrete_types(self):
        message = InputRichMessage.model_validate({"blocks": [_nested_blockquote(depth=4)]})

        node = message.blocks[0]
        for _ in range(5):  # 1 outer + 4 nested blockquotes
            assert isinstance(node, InputRichBlockBlockQuotation)
            node = node.blocks[0]
        assert isinstance(node, InputRichBlockParagraph)
        assert node.text == "leaf"


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="performance guard relies on SIGALRM (POSIX only)",
)
def test_nested_input_rich_block_validation_is_not_exponential():
    # Same guard as test_nested_rich_block_validation_is_not_exponential, but
    # for the input-side mirror InputRichBlockUnion / InputRichMessage.
    payload = {"blocks": [_nested_blockquote(depth=30)]}

    def _abort(signum, frame):
        raise TimeoutError

    previous_handler = signal.signal(signal.SIGALRM, _abort)
    try:
        signal.setitimer(signal.ITIMER_REAL, 5.0)
        start = time.perf_counter()
        InputRichMessage.model_validate(payload)
        elapsed = time.perf_counter() - start
    except TimeoutError:
        pytest.fail(
            "Validating a depth-30 nested InputRichBlock exceeded 5s -- "
            "InputRichBlockUnion likely regressed to a non-discriminated (exponential) union."
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)

    assert elapsed < 1.0


class TestMethodFieldDiscriminatedUnion:
    def test_input_media_union_field_selects_member_by_tag(self):
        method = EditMessageMedia.model_validate(
            {"media": {"type": "photo", "media": "https://example.org/photo.jpg"}}
        )
        assert isinstance(method.media, InputMediaPhoto)

    def test_input_media_union_field_rejects_unknown_tag(self):
        with pytest.raises(ValidationError) as exc_info:
            EditMessageMedia.model_validate({"media": {"type": "nope", "media": "x"}})

        errors = exc_info.value.errors()
        assert errors[0]["type"] == "union_tag_invalid"

    def test_inline_query_result_union_field_is_not_discriminated(self):
        # InlineQueryResultUnion declares ``type`` in the generator config, but
        # cached/non-cached members share tag values (e.g. both photo variants
        # use ``type="photo"``), so it must stay a plain smart union. A field
        # forcing a discriminator here would crash Pydantic at schema build time.
        method = AnswerWebAppQuery.model_validate(
            {
                "web_app_query_id": "q",
                "result": {
                    "type": "article",
                    "id": "1",
                    "title": "t",
                    "input_message_content": {"message_text": "x"},
                },
            }
        )
        assert type(method.result).__name__ == "InlineQueryResultArticle"
