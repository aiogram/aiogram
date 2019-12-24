from typing import List, Optional

import pytest
from aiogram.api.types import MessageEntity, User
from aiogram.utils.text_decorations import TextDecoration, html, markdown


class TestTextDecoration:
    @pytest.mark.parametrize(
        "decorator,entity,result",
        [
            [html, MessageEntity(type="url", offset=0, length=5), "test"],
            [
                html,
                MessageEntity(type="text_link", offset=0, length=5, url="https://aiogram.dev"),
                '<a href="https://aiogram.dev">test</a>',
            ],
            [html, MessageEntity(type="bold", offset=0, length=5), "<b>test</b>"],
            [html, MessageEntity(type="italic", offset=0, length=5), "<i>test</i>"],
            [html, MessageEntity(type="code", offset=0, length=5), "<code>test</code>"],
            [html, MessageEntity(type="pre", offset=0, length=5), "<pre>test</pre>"],
            [html, MessageEntity(type="underline", offset=0, length=5), "<u>test</u>"],
            [html, MessageEntity(type="strikethrough", offset=0, length=5), "<s>test</s>"],
            [html, MessageEntity(type="hashtag", offset=0, length=5), "test"],
            [html, MessageEntity(type="cashtag", offset=0, length=5), "test"],
            [html, MessageEntity(type="bot_command", offset=0, length=5), "test"],
            [html, MessageEntity(type="email", offset=0, length=5), "test"],
            [html, MessageEntity(type="phone_number", offset=0, length=5), "test"],
            [
                html,
                MessageEntity(
                    type="text_mention",
                    offset=0,
                    length=5,
                    user=User(id=42, first_name="Test", is_bot=False),
                ),
                '<a href="tg://user?id=42">test</a>',
            ],
            [html, MessageEntity(type="url", offset=0, length=5), "test"],
            [
                html,
                MessageEntity(type="text_link", offset=0, length=5, url="https://aiogram.dev"),
                '<a href="https://aiogram.dev">test</a>',
            ],
            [markdown, MessageEntity(type="bold", offset=0, length=5), "*test*"],
            [markdown, MessageEntity(type="italic", offset=0, length=5), "_test_"],
            [markdown, MessageEntity(type="code", offset=0, length=5), "`test`"],
            [markdown, MessageEntity(type="pre", offset=0, length=5), "```test```"],
            [markdown, MessageEntity(type="underline", offset=0, length=5), "--test--"],
            [markdown, MessageEntity(type="strikethrough", offset=0, length=5), "~~test~~"],
            [markdown, MessageEntity(type="hashtag", offset=0, length=5), "test"],
            [markdown, MessageEntity(type="cashtag", offset=0, length=5), "test"],
            [markdown, MessageEntity(type="bot_command", offset=0, length=5), "test"],
            [markdown, MessageEntity(type="email", offset=0, length=5), "test"],
            [markdown, MessageEntity(type="phone_number", offset=0, length=5), "test"],
            [
                markdown,
                MessageEntity(
                    type="text_mention",
                    offset=0,
                    length=5,
                    user=User(id=42, first_name="Test", is_bot=False),
                ),
                "[test](tg://user?id=42)",
            ],
        ],
    )
    def test_apply_single_entity(
        self, decorator: TextDecoration, entity: MessageEntity, result: str
    ):
        assert decorator.apply_entity(entity, "test") == result

    @pytest.mark.parametrize(
        "decorator,before,after",
        [
            [html, "test", "test"],
            [html, "test < test", "test &lt; test"],
            [html, "test > test", "test &gt; test"],
            [html, "test & test", "test &amp; test"],
            [html, "test @ test", "test @ test"],
            [markdown, "test", "test"],
            [markdown, "[test]", "\\[test]"],
            [markdown, "test ` test", "test \\` test"],
            [markdown, "test * test", "test \\* test"],
            [markdown, "test _ test", "test \\_ test"],
        ],
    )
    def test_quote(self, decorator: TextDecoration, before: str, after: str):
        assert decorator.quote(before) == after

    @pytest.mark.parametrize(
        "decorator,text,entities,result",
        [
            [html, "test", None, "test"],
            [
                html,
                "test1 test2 test3 test4 test5 test6 test7",
                [
                    MessageEntity(type="bold", offset=6, length=29),
                    MessageEntity(type="underline", offset=12, length=5),
                    MessageEntity(type="italic", offset=24, length=5),
                ],
                "test1 <b>test2 <u>test3</u> test4 <i>test5</i> test6</b> test7",
            ],
            [
                html,
                "test1 test2 test3 test4 test5",
                [
                    MessageEntity(type="bold", offset=6, length=17),
                    MessageEntity(type="underline", offset=12, length=5),
                ],
                "test1 <b>test2 <u>test3</u> test4</b> test5",
            ],
            [
                html,
                "test1 test2 test3 test4",
                [
                    MessageEntity(type="bold", offset=6, length=11),
                    MessageEntity(type="underline", offset=12, length=5),
                ],
                "test1 <b>test2 <u>test3</u></b> test4",
            ],
            [
                html,
                "test1 test2  test3",
                [MessageEntity(type="bold", offset=6, length=6),],
                "test1 <b>test2 </b> test3",
            ],
            [
                html,
                "test1 test2",
                [MessageEntity(type="bold", offset=0, length=5),],
                "<b>test1</b> test2",
            ],
            # [
            #     html,
            #     "test te👍🏿st test",
            #     [MessageEntity(type="bold", offset=5, length=6, url=None, user=None),],
            #     "test <b>te👍🏿st</b> test",
            # ],
        ],
    )
    def test_unparse(
        self,
        decorator: TextDecoration,
        text: str,
        entities: Optional[List[MessageEntity]],
        result: str,
    ):
        assert decorator.unparse(text, entities) == result
