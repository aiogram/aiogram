import pytest

from aiogram.enums import MessageEntityType
from aiogram.types import MessageEntity, User
from aiogram.utils.formatting import (
    BlockQuote,
    Bold,
    BotCommand,
    CashTag,
    Code,
    CustomEmoji,
    Email,
    ExpandableBlockQuote,
    HashTag,
    Italic,
    PhoneNumber,
    Pre,
    Spoiler,
    Strikethrough,
    Text,
    TextLink,
    TextMention,
    Underline,
    Url,
    _apply_entity,
    as_key_value,
    as_line,
    as_list,
    as_marked_list,
    as_marked_section,
    as_numbered_list,
    as_numbered_section,
    as_section,
)
from aiogram.utils.text_decorations import html_decoration


class TestNode:
    @pytest.mark.parametrize(
        "node,result",
        [
            [
                Text("test"),
                "test",
            ],
            [
                HashTag("#test"),
                "#test",
            ],
            [
                CashTag("$TEST"),
                "$TEST",
            ],
            [
                BotCommand("/test"),
                "/test",
            ],
            [
                Url("https://example.com"),
                "https://example.com",
            ],
            [
                Email("test@example.com"),
                "test@example.com",
            ],
            [
                PhoneNumber("test"),
                "test",
            ],
            [
                Bold("test"),
                "<b>test</b>",
            ],
            [
                Italic("test"),
                "<i>test</i>",
            ],
            [
                Underline("test"),
                "<u>test</u>",
            ],
            [
                Strikethrough("test"),
                "<s>test</s>",
            ],
            [
                Spoiler("test"),
                "<tg-spoiler>test</tg-spoiler>",
            ],
            [
                Code("test"),
                "<code>test</code>",
            ],
            [
                Pre("test", language="python"),
                '<pre><code class="language-python">test</code></pre>',
            ],
            [
                TextLink("test", url="https://example.com"),
                '<a href="https://example.com">test</a>',
            ],
            [
                TextMention("test", user=User(id=42, is_bot=False, first_name="Test")),
                '<a href="tg://user?id=42">test</a>',
            ],
            [
                CustomEmoji("test", custom_emoji_id="42"),
                '<tg-emoji emoji-id="42">test</tg-emoji>',
            ],
            [
                BlockQuote("test"),
                "<blockquote>test</blockquote>",
            ],
            [
                ExpandableBlockQuote("test"),
                "<blockquote expandable>test</blockquote>",
            ],
        ],
    )
    def test_render_plain_only(self, node: Text, result: str):
        text, entities = node.render()
        if node.type:
            assert len(entities) == 1
            entity = entities[0]
            assert entity.type == node.type

        content = html_decoration.unparse(text, entities)
        assert content == result

    def test_render_text(self):
        node = Text("Hello, ", "World", "!")
        text, entities = node.render()
        assert text == "Hello, World!"
        assert not entities

    def test_render_nested(self):
        node = Text(
            Text("Hello, ", Bold("World"), "!"),
            "\n",
            Text(Bold("This ", Underline("is"), " test", Italic("!"))),
            "\n",
            HashTag("#test"),
        )
        text, entities = node.render()
        assert text == "Hello, World!\nThis is test!\n#test"
        assert entities == [
            MessageEntity(type="bold", offset=7, length=5),
            MessageEntity(type="bold", offset=14, length=13),
            MessageEntity(type="underline", offset=19, length=2),
            MessageEntity(type="italic", offset=26, length=1),
            MessageEntity(type="hashtag", offset=28, length=5),
        ]

    def test_as_kwargs_default(self):
        node = Text("Hello, ", Bold("World"), "!")
        result = node.as_kwargs()
        assert "text" in result
        assert "entities" in result
        assert "parse_mode" in result

    def test_as_kwargs_custom(self):
        node = Text("Hello, ", Bold("World"), "!")
        result = node.as_kwargs(
            text_key="caption",
            entities_key="custom_entities",
            parse_mode_key="custom_parse_mode",
        )
        assert "text" not in result
        assert "caption" in result
        assert "entities" not in result
        assert "custom_entities" in result
        assert "parse_mode" not in result
        assert "custom_parse_mode" in result

    def test_as_caption_kwargs(self):
        node = Text("Hello, ", Bold("World"), "!")
        result = node.as_caption_kwargs()
        assert "caption" in result
        assert "caption_entities" in result
        assert "parse_mode" in result

    def test_as_poll_question_kwargs(self):
        node = Text("Hello, ", Bold("World"), "!")
        result = node.as_poll_question_kwargs()
        assert "question" in result
        assert "question_entities" in result
        assert "question_parse_mode" in result

    def test_as_poll_explanation_kwargs(self):
        node = Text("Hello, ", Bold("World"), "!")
        result = node.as_poll_explanation_kwargs()
        assert "explanation" in result
        assert "explanation_entities" in result
        assert "explanation_parse_mode" in result

    def test_as_as_gift_text_kwargs_kwargs(self):
        node = Text("Hello, ", Bold("World"), "!")
        result = node.as_gift_text_kwargs()
        assert "text" in result
        assert "text_entities" in result
        assert "text_parse_mode" in result


    def test_as_html(self):
        node = Text("Hello, ", Bold("World"), "!")
        assert node.as_html() == "Hello, <b>World</b>!"

    def test_as_markdown(self):
        node = Text("Hello, ", Bold("World"), "!")
        assert node.as_markdown() == r"Hello, *World*\!"

    def test_replace(self):
        node0 = Text("test0", param0="test1")
        node1 = node0.replace("test1", "test2", param1="test1")
        assert node0._body != node1._body
        assert node0._params != node1._params
        assert "param1" not in node0._params
        assert "param1" in node1._params

    def test_add(self):
        node0 = Text("Hello")
        node1 = Bold("World")

        node2 = node0 + Text(", ") + node1 + "!"
        assert node0 != node2
        assert node1 != node2
        assert len(node0._body) == 1
        assert len(node1._body) == 1
        assert len(node2._body) == 3

        text, entities = node2.render()
        assert text == "Hello, World!"

    def test_getitem_position(self):
        node = Text("Hello, ", Bold("World"), "!")
        with pytest.raises(TypeError):
            node[2]

    def test_getitem_empty_slice(self):
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[:]
        assert new_node is not node
        assert isinstance(new_node, Text)
        assert new_node._body == node._body

    def test_getitem_slice_zero(self):
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[2:2]
        assert node is not new_node
        assert isinstance(new_node, Text)
        assert not new_node._body

    def test_getitem_slice_simple(self):
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[2:10]
        assert isinstance(new_node, Text)
        text, entities = new_node.render()
        assert text == "llo, Wor"
        assert len(entities) == 1
        assert entities[0].type == MessageEntityType.BOLD

    def test_getitem_slice_inside_child(self):
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[8:10]
        assert isinstance(new_node, Text)
        text, entities = new_node.render()
        assert text == "or"
        assert len(entities) == 1
        assert entities[0].type == MessageEntityType.BOLD

    def test_getitem_slice_tail(self):
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[12:13]
        assert isinstance(new_node, Text)
        text, entities = new_node.render()
        assert text == "!"
        assert not entities

    def test_from_entities(self):
        # Most of the cases covered by text_decorations module

        node = Strikethrough.from_entities(
            text="test1 test2 test3 test4 test5 test6 test7",
            entities=[
                MessageEntity(type="bold", offset=6, length=29),
                MessageEntity(type="underline", offset=12, length=5),
                MessageEntity(type="italic", offset=24, length=5),
            ],
        )
        assert len(node._body) == 3
        assert isinstance(node, Strikethrough)
        rendered = node.as_html()
        assert rendered == "<s>test1 <b>test2 <u>test3</u> test4 <i>test5</i> test6</b> test7</s>"

    def test_pretty_string(self):
        node = Strikethrough.from_entities(
            text="X",
            entities=[
                MessageEntity(
                    type=MessageEntityType.CUSTOM_EMOJI,
                    offset=0,
                    length=1,
                    custom_emoji_id="42",
                ),
            ],
        )
        assert (
            node.as_pretty_string(indent=True)
            == """Strikethrough(
    CustomEmoji(
        'X',
        custom_emoji_id='42'
    )
)"""
        )


class TestHashTag:
    def test_only_one_element_in_body(self):
        with pytest.raises(ValueError):
            HashTag("test", "test")

    def test_body_is_not_str(self):
        with pytest.raises(ValueError):
            HashTag(Text("test"))

    def test_with_no_prefix(self):
        node = HashTag("test")
        assert node._body == ("#test",)

    def test_with_prefix(self):
        node = HashTag("#test")
        assert node._body == ("#test",)


class TestCashTag:
    def test_only_one_element_in_body(self):
        with pytest.raises(ValueError):
            CashTag("test", "test")

    def test_body_is_not_str(self):
        with pytest.raises(ValueError):
            CashTag(Text("test"))

    def test_with_no_prefix(self):
        node = CashTag("USD")
        assert node._body == ("$USD",)

    def test_with_prefix(self):
        node = CashTag("$USD")
        assert node._body == ("$USD",)


class TestUtils:
    def test_apply_entity(self):
        node = _apply_entity(
            MessageEntity(type=MessageEntityType.BOLD, offset=0, length=4), "test"
        )
        assert isinstance(node, Bold)
        assert node._body == ("test",)

    def test_as_line(self):
        node = as_line("test", "test", "test")
        assert isinstance(node, Text)
        assert len(node._body) == 4  # 3 + '\n'

    def test_line_with_sep(self):
        node = as_line("test", "test", "test", sep=" ")
        assert isinstance(node, Text)
        assert len(node._body) == 6  # 3 + 2 * ' ' + '\n'

    def test_as_line_single_element_with_sep(self):
        node = as_line("test", sep=" ")
        assert isinstance(node, Text)
        assert len(node._body) == 2  # 1 + '\n'

    def test_as_list(self):
        node = as_list("test", "test", "test")
        assert isinstance(node, Text)
        assert len(node._body) == 5  # 3 + 2 * '\n' between lines

    def test_as_marked_list(self):
        node = as_marked_list("test 1", "test 2", "test 3")
        assert node.as_html() == "- test 1\n- test 2\n- test 3"

    def test_as_numbered_list(self):
        node = as_numbered_list("test 1", "test 2", "test 3", start=5)
        assert node.as_html() == "5. test 1\n6. test 2\n7. test 3"

    def test_as_section(self):
        node = as_section("title", "test 1", "test 2", "test 3")
        assert node.as_html() == "title\ntest 1test 2test 3"

    def test_as_marked_section(self):
        node = as_marked_section("Section", "test 1", "test 2", "test 3")
        assert node.as_html() == "Section\n- test 1\n- test 2\n- test 3"

    def test_as_numbered_section(self):
        node = as_numbered_section("Section", "test 1", "test 2", "test 3", start=5)
        assert node.as_html() == "Section\n5. test 1\n6. test 2\n7. test 3"

    def test_as_key_value(self):
        node = as_key_value("key", "test 1")
        assert node.as_html() == "<b>key:</b> test 1"
