import pytest

from aiogram.types import MessageEntity, User
from aiogram.utils.text_decorations import (
    TextDecoration,
    html_decoration,
    markdown_decoration,
)


class TestTextDecoration:
    @pytest.mark.parametrize(
        "decorator,entity,result",
        [
            [html_decoration, MessageEntity(type="url", offset=0, length=5), "test"],
            [
                html_decoration,
                MessageEntity(type="text_link", offset=0, length=5, url="https://aiogram.dev"),
                '<a href="https://aiogram.dev">test</a>',
            ],
            [html_decoration, MessageEntity(type="bold", offset=0, length=5), "<b>test</b>"],
            [html_decoration, MessageEntity(type="italic", offset=0, length=5), "<i>test</i>"],
            [html_decoration, MessageEntity(type="code", offset=0, length=5), "<code>test</code>"],
            [html_decoration, MessageEntity(type="pre", offset=0, length=5), "<pre>test</pre>"],
            [
                html_decoration,
                MessageEntity(type="pre", offset=0, length=5, language="python"),
                '<pre><code class="language-python">test</code></pre>',
            ],
            [html_decoration, MessageEntity(type="underline", offset=0, length=5), "<u>test</u>"],
            [
                html_decoration,
                MessageEntity(type="strikethrough", offset=0, length=5),
                "<s>test</s>",
            ],
            [html_decoration, MessageEntity(type="hashtag", offset=0, length=5), "test"],
            [html_decoration, MessageEntity(type="cashtag", offset=0, length=5), "test"],
            [html_decoration, MessageEntity(type="bot_command", offset=0, length=5), "test"],
            [html_decoration, MessageEntity(type="email", offset=0, length=5), "test"],
            [html_decoration, MessageEntity(type="phone_number", offset=0, length=5), "test"],
            [
                html_decoration,
                MessageEntity(
                    type="text_mention",
                    offset=0,
                    length=5,
                    user=User(id=42, first_name="Test", is_bot=False),
                ),
                '<a href="tg://user?id=42">test</a>',
            ],
            [
                html_decoration,
                MessageEntity(type="spoiler", offset=0, length=5),
                "<tg-spoiler>test</tg-spoiler>",
            ],
            [
                html_decoration,
                MessageEntity(type="custom_emoji", offset=0, length=5, custom_emoji_id="42"),
                '<tg-emoji emoji-id="42">test</tg-emoji>',
            ],
            [
                html_decoration,
                MessageEntity(type="blockquote", offset=0, length=5),
                "<blockquote>test</blockquote>",
            ],
            [
                html_decoration,
                MessageEntity(type="expandable_blockquote", offset=0, length=5),
                "<blockquote expandable>test</blockquote>",
            ],
            [markdown_decoration, MessageEntity(type="url", offset=0, length=5), "test"],
            [
                markdown_decoration,
                MessageEntity(type="text_link", offset=0, length=5, url="https://aiogram.dev"),
                "[test](https://aiogram.dev)",
            ],
            [markdown_decoration, MessageEntity(type="bold", offset=0, length=5), "*test*"],
            [markdown_decoration, MessageEntity(type="italic", offset=0, length=5), "_\rtest_\r"],
            [markdown_decoration, MessageEntity(type="code", offset=0, length=5), "`test`"],
            [markdown_decoration, MessageEntity(type="pre", offset=0, length=5), "```\ntest\n```"],
            [
                markdown_decoration,
                MessageEntity(type="pre", offset=0, length=5, language="python"),
                "```python\ntest\n```",
            ],
            [
                markdown_decoration,
                MessageEntity(type="underline", offset=0, length=5),
                "__\rtest__\r",
            ],
            [
                markdown_decoration,
                MessageEntity(type="strikethrough", offset=0, length=5),
                "~test~",
            ],
            [markdown_decoration, MessageEntity(type="hashtag", offset=0, length=5), "test"],
            [markdown_decoration, MessageEntity(type="cashtag", offset=0, length=5), "test"],
            [markdown_decoration, MessageEntity(type="bot_command", offset=0, length=5), "test"],
            [markdown_decoration, MessageEntity(type="email", offset=0, length=5), "test"],
            [markdown_decoration, MessageEntity(type="phone_number", offset=0, length=5), "test"],
            [markdown_decoration, MessageEntity(type="spoiler", offset=0, length=5), "||test||"],
            [
                markdown_decoration,
                MessageEntity(type="custom_emoji", offset=0, length=5, custom_emoji_id="42"),
                "![test](tg://emoji?id=42)",
            ],
            [
                markdown_decoration,
                MessageEntity(
                    type="text_mention",
                    offset=0,
                    length=5,
                    user=User(id=42, first_name="Test", is_bot=False),
                ),
                "[test](tg://user?id=42)",
            ],
            [
                markdown_decoration,
                MessageEntity(type="blockquote", offset=0, length=5),
                ">test",
            ],
            [
                markdown_decoration,
                MessageEntity(type="expandable_blockquote", offset=0, length=5),
                ">test||",
            ],
        ],
    )
    def test_apply_single_entity(
        self, decorator: TextDecoration, entity: MessageEntity, result: str
    ):
        assert decorator.apply_entity(entity, "test") == result

    def test_unknown_apply_entity(self):
        assert (
            html_decoration.apply_entity(
                MessageEntity(type="unknown", offset=0, length=5), "<test>"
            )
            == "&lt;test&gt;"
        )

    @pytest.mark.parametrize(
        "decorator,before,after",
        [
            [html_decoration, "test", "test"],
            [html_decoration, "test < test", "test &lt; test"],
            [html_decoration, "test > test", "test &gt; test"],
            [html_decoration, "test & test", "test &amp; test"],
            [html_decoration, "test @ test", "test @ test"],
            [markdown_decoration, "test", "test"],
            [markdown_decoration, "[test]", "\\[test\\]"],
            [markdown_decoration, "test ` test", "test \\` test"],
            [markdown_decoration, "test * test", "test \\* test"],
            [markdown_decoration, "test _ test", "test \\_ test"],
        ],
    )
    def test_quote(self, decorator: TextDecoration, before: str, after: str):
        assert decorator.quote(before) == after

    @pytest.mark.parametrize(
        "decorator,text,entities,result",
        [
            [html_decoration, "test", None, "test"],
            [html_decoration, "test", [], "test"],
            [
                html_decoration,
                "test1 test2 test3 test4 test5 test6 test7",
                [
                    MessageEntity(type="bold", offset=6, length=29),
                    MessageEntity(type="underline", offset=12, length=5),
                    MessageEntity(type="italic", offset=24, length=5),
                ],
                "test1 <b>test2 <u>test3</u> test4 <i>test5</i> test6</b> test7",
            ],
            [
                html_decoration,
                "test1 test2 test3 test4 test5",
                [
                    MessageEntity(type="bold", offset=6, length=17),
                    MessageEntity(type="underline", offset=12, length=5),
                ],
                "test1 <b>test2 <u>test3</u> test4</b> test5",
            ],
            [
                html_decoration,
                "test1 test2 test3 test4",
                [
                    MessageEntity(type="bold", offset=6, length=11),
                    MessageEntity(type="underline", offset=12, length=5),
                ],
                "test1 <b>test2 <u>test3</u></b> test4",
            ],
            [
                html_decoration,
                "test1 test2 test3",
                [MessageEntity(type="bold", offset=6, length=5)],
                "test1 <b>test2</b> test3",
            ],
            [
                html_decoration,
                "test1 test2",
                [MessageEntity(type="bold", offset=0, length=5)],
                "<b>test1</b> test2",
            ],
            [
                html_decoration,
                "strike bold",
                [
                    MessageEntity(type="strikethrough", offset=0, length=6),
                    MessageEntity(type="bold", offset=7, length=4),
                ],
                "<s>strike</s> <b>bold</b>",
            ],
            [
                html_decoration,
                "test",
                [
                    MessageEntity(type="strikethrough", offset=0, length=5),
                    MessageEntity(type="bold", offset=0, length=5),
                ],
                "<s><b>test</b></s>",
            ],
            [
                html_decoration,
                "strikeboldunder",
                [
                    MessageEntity(type="strikethrough", offset=0, length=15),
                    MessageEntity(type="bold", offset=6, length=9),
                    MessageEntity(type="underline", offset=10, length=5),
                ],
                "<s>strike<b>bold<u>under</u></b></s>",
            ],
            [
                html_decoration,
                "@username",
                [
                    MessageEntity(type="mention", offset=0, length=9),
                    MessageEntity(type="bold", offset=0, length=9),
                ],
                "<b>@username</b>",
            ],
            [
                html_decoration,
                "/command",
                [
                    MessageEntity(type="bot_command", offset=0, length=8),
                    MessageEntity(type="bold", offset=0, length=8),
                ],
                "<b>/command</b>",
            ],
            [
                html_decoration,
                "+1-212-555-0123",
                [
                    MessageEntity(type="phone_number", offset=0, length=15),
                    MessageEntity(type="bold", offset=0, length=15),
                ],
                "<b>+1-212-555-0123</b>",
            ],
            [
                html_decoration,
                "test te👍🏿st test",
                [MessageEntity(type="bold", offset=5, length=8, url=None, user=None)],
                "test <b>te👍🏿st</b> test",
            ],
            [
                html_decoration,
                "👋🏾 Hi!",
                [MessageEntity(type="bold", offset=0, length=8, url=None, user=None)],
                "<b>👋🏾 Hi!</b>",
            ],
            [
                html_decoration,
                "#test",
                [
                    MessageEntity(type="hashtag", offset=0, length=5),
                    MessageEntity(type="bold", offset=0, length=5),
                ],
                "<b>#test</b>",
            ],
            [
                html_decoration,
                "$TEST",
                [
                    MessageEntity(type="cashtag", offset=0, length=5),
                    MessageEntity(type="bold", offset=0, length=5),
                ],
                "<b>$TEST</b>",
            ],
            [
                html_decoration,
                "test@example.com",
                [
                    MessageEntity(type="email", offset=0, length=16),
                    MessageEntity(type="bold", offset=0, length=16),
                ],
                "<b>test@example.com</b>",
            ],
        ],
    )
    def test_unparse(
        self,
        decorator: TextDecoration,
        text: str,
        entities: list[MessageEntity] | None,
        result: str,
    ):
        assert decorator.unparse(text, entities) == result
