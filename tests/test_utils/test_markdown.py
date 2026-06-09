from collections.abc import Callable
from typing import Any

import pytest

from aiogram.utils.markdown import (
    blockquote,
    bold,
    code,
    hblockquote,
    hbold,
    hcode,
    hide_link,
    hitalic,
    hlink,
    hpre,
    hstrikethrough,
    hunderline,
    italic,
    link,
    pre,
    strikethrough,
    text,
    underline,
)


class TestMarkdown:
    @pytest.mark.parametrize(
        "func,args,sep,result",
        [
            [text, ("test", "test"), " ", "test test"],
            [text, ("test", "test"), "\n", "test\ntest"],
            [text, ("test", "test"), None, "test test"],
            [bold, ("test", "test"), " ", "*test test*"],
            [hbold, ("test", "test"), " ", "<b>test test</b>"],
            [italic, ("test", "test"), " ", "_\rtest test_\r"],
            [hitalic, ("test", "test"), " ", "<i>test test</i>"],
            [code, ("test", "test"), " ", "`test test`"],
            [hcode, ("test", "test"), " ", "<code>test test</code>"],
            [pre, ("test", "test"), " ", "```\ntest test\n```"],
            [hpre, ("test", "test"), " ", "<pre>test test</pre>"],
            [underline, ("test", "test"), " ", "__\rtest test__\r"],
            [hunderline, ("test", "test"), " ", "<u>test test</u>"],
            [strikethrough, ("test", "test"), " ", "~test test~"],
            [hstrikethrough, ("test", "test"), " ", "<s>test test</s>"],
            [link, ("test", "https://aiogram.dev"), None, "[test](https://aiogram.dev)"],
            [
                hlink,
                ("test", "https://aiogram.dev"),
                None,
                '<a href="https://aiogram.dev">test</a>',
            ],
            [
                hide_link,
                ("https://aiogram.dev",),
                None,
                '<a href="https://aiogram.dev">&#8203;</a>',
            ],
            [blockquote, ("spam", "eggs"), " ", ">spam eggs"],
            pytest.param(
                blockquote,
                ("spam", "eggs"),
                "\n",
                ">spam\n>eggs",
                id="Markdown V2 blockquote multiline",
            ),
            [hblockquote, ("spam", "eggs"), " ", "<blockquote>spam eggs</blockquote>"],
            pytest.param(
                hblockquote,
                ("spam", "eggs"),
                "\n",
                "<blockquote>spam\neggs</blockquote>",
                id="HTML blockquote multiline",
            ),
        ],
    )
    def test_formatter(
        self, func: Callable[[Any], Any], args: tuple[str], sep: str | None, result: str
    ):
        assert func(*args, **({"sep": sep} if sep is not None else {})) == result  # type: ignore
