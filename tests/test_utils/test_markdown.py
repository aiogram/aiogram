from typing import Any, Callable, Optional, Tuple

import pytest

from aiogram.utils import markdown


class TestMarkdown:
    @pytest.mark.parametrize(
        "func,args,sep,result",
        [
            [markdown.text, ("test", "test"), " ", "test test"],
            [markdown.text, ("test", "test"), "\n", "test\ntest"],
            [markdown.text, ("test", "test"), None, "test test"],
            [markdown.bold, ("test", "test"), " ", "*test test*"],
            [markdown.hbold, ("test", "test"), " ", "<b>test test</b>"],
            [markdown.italic, ("test", "test"), " ", "_test test_\r"],
            [markdown.hitalic, ("test", "test"), " ", "<i>test test</i>"],
            [markdown.code, ("test", "test"), " ", "`test test`"],
            [markdown.hcode, ("test", "test"), " ", "<code>test test</code>"],
            [markdown.pre, ("test", "test"), " ", "```test test```"],
            [markdown.hpre, ("test", "test"), " ", "<pre>test test</pre>"],
            [markdown.underline, ("test", "test"), " ", "__test test__"],
            [markdown.hunderline, ("test", "test"), " ", "<u>test test</u>"],
            [markdown.strikethrough, ("test", "test"), " ", "~test test~"],
            [markdown.hstrikethrough, ("test", "test"), " ", "<s>test test</s>"],
            [markdown.link, ("test", "https://aiogram.dev"), None, "[test](https://aiogram.dev)"],
            [
                markdown.hlink,
                ("test", "https://aiogram.dev"),
                None,
                '<a href="https://aiogram.dev">test</a>',
            ],
            [
                markdown.hide_link,
                ("https://aiogram.dev",),
                None,
                '<a href="https://aiogram.dev">&#8203;</a>',
            ],
        ],
    )
    def test_formatter(
        self, func: Callable[[Any], Any], args: Tuple[str], sep: Optional[str], result: str
    ):
        assert func(*args, **({"sep": sep} if sep is not None else {})) == result  # type: ignore
