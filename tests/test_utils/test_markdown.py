import pytest

from aiogram.utils import markdown


class TestMarkdownEscape:
    @staticmethod
    def test_equality_sign_is_escaped():
        if markdown.escape_md(r"e = mc2") != r"e \= mc2":
            raise AssertionError

    @staticmethod
    def test_pre_escaped():
        if markdown.escape_md(r"hello\.") != r"hello\\\.":
            raise AssertionError
