from typing import Any

import pytest

from aiogram.utils.link import (
    BRANCH,
    create_channel_bot_link,
    create_telegram_link,
    create_tg_link,
    docs_url,
)


class TestLink:
    @pytest.mark.parametrize(
        "base,params,result",
        [["user", {"id": 42}, "tg://user?id=42"]],
    )
    def test_create_tg_link(self, base: str, params: dict[str, Any], result: str):
        assert create_tg_link(base, **params) == result

    @pytest.mark.parametrize(
        "base,params,result",
        [
            ["username", {}, "https://t.me/username"],
            ["username", {"start": "test"}, "https://t.me/username?start=test"],
        ],
    )
    def test_create_telegram_link(self, base: str, params: dict[str, Any], result: str):
        assert create_telegram_link(base, **params) == result

    def test_fragment(self):
        assert (
            docs_url("test.html", fragment_="test")
            == f"https://docs.aiogram.dev/en/{BRANCH}/test.html#test"
        )

    def test_docs(self):
        assert docs_url("test.html") == f"https://docs.aiogram.dev/en/{BRANCH}/test.html"


RIGHTS = [
    "change_info",
    "post_messages",
    "edit_messages",
    "delete_messages",
    "restrict_members",
    "invite_users",
    "pin_messages",
    "manage_topics",
    "promote_members",
    "manage_video_chats",
    "anonymous",
    "manage_chat",
    "post_stories",
    "edit_stories",
    "delete_stories",
    "manage_direct_messages",
    "manage_tags",
]


class TestCreateChannelBotLink:
    def test_without_rights(self):
        assert create_channel_bot_link("test_bot") == "https://t.me/test_bot"

    @pytest.mark.parametrize("right", RIGHTS)
    def test_single_right(self, right: str):
        assert (
            create_channel_bot_link("test_bot", **{right: True})
            == f"https://t.me/test_bot?startchannel&admin={right}"
        )

    def test_all_rights(self):
        link = create_channel_bot_link("test_bot", **dict.fromkeys(RIGHTS, True))
        assert link == "https://t.me/test_bot?startchannel&admin=" + "+".join(RIGHTS)

    def test_parameter_deprecated(self):
        with pytest.warns(DeprecationWarning, match="'parameter'"):
            link = create_channel_bot_link("test_bot", parameter="parameter in group")
        assert link == "https://t.me/test_bot?startgroup=parameter+in+group"

    def test_parameter_with_rights_deprecated(self):
        with pytest.warns(DeprecationWarning):
            link = create_channel_bot_link(
                "test_bot", parameter="ref", post_messages=True, edit_messages=True
            )
        assert link == "https://t.me/test_bot?startgroup=ref&admin=post_messages+edit_messages"
