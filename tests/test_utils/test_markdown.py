import pytest

from aiogram.utils import markdown


class TestMarkdownEscape:
    def test_equality_sign_is_escaped(self):
        if markdown.escape_md(r"e = mc2") != r"e \= mc2":
            raise AssertionError

    def test_pre_escaped(self):
        if markdown.escape_md(r"hello\.") != r"hello\\\.":
            raise AssertionError
