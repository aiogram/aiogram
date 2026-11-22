import pytest

from aiogram.methods import GetMe
from aiogram.types import (
    BotFullInfo,
    InputRichBlockExpandableBlockQuotation,
    RichBlockExpandableBlockQuotation,
    RichBlockParagraph,
    User,
    WriteAccessAllowed,
)
from tests.mocked_bot import MockedBot, bot_full_info


def test_bot_full_info_optional_fields():
    info = bot_full_info(
        username="bot",
        active_usernames=["bot", "other_bot"],
        inline_query_placeholder="Search",
        needs_inline_query_location=True,
        has_topic_sidebar=True,
    )
    assert info.active_usernames == ["bot", "other_bot"]
    assert info.inline_query_placeholder == "Search"
    assert info.needs_inline_query_location is True
    assert info.has_topic_sidebar is True


def test_write_access_allowed_inviter():
    owner = User(id=1, is_bot=False, first_name="Owner")
    assert WriteAccessAllowed(inviter=owner).inviter == owner
    assert WriteAccessAllowed().inviter is None


def test_expandable_block_quotation_blocks():
    block = RichBlockExpandableBlockQuotation.model_validate(
        {
            "type": "expandable_blockquote",
            "blocks": [{"type": "paragraph", "text": "hi"}],
        }
    )
    assert isinstance(block.blocks[0], RichBlockParagraph)
    assert block.text is None
    assert InputRichBlockExpandableBlockQuotation.model_fields["blocks"].is_required()


class TestBotMe:
    async def test_me_is_what_get_me_returned(self, bot: MockedBot):
        bot._me = None
        info = bot_full_info(username="tbot", id=7)
        bot.add_result_for(GetMe, ok=True, result=info)
        assert await bot.me() == info
        assert await bot.me() is await bot.me()
        assert len(bot.session.requests) == 1

    @pytest.mark.parametrize(
        "username,active,expected",
        [
            ("tbot", ["tbot_AI", "tbot"], ("tbot", "tbot_AI")),
            ("tbot", ["TBot", "tbot_ai", "TBOT_AI"], ("tbot", "tbot_ai")),
            ("tbot", None, ("tbot",)),
            (None, ["tbot_ai"], ("tbot_ai",)),
            (None, None, ()),
        ],
    )
    async def test_usernames(self, bot: MockedBot, username, active, expected):
        bot._me = bot_full_info(username=username, active_usernames=active)
        assert await bot.usernames() == expected
        assert not bot.session.requests


def test_bot_full_info_user_like_helpers():
    info = bot_full_info(id=42, first_name="Bot")
    assert info.full_name == "Bot"
    assert info.url == "tg://user?id=42"
    assert info.mention_html() == '<a href="tg://user?id=42">Bot</a>'
    assert info.mention_html("x") == '<a href="tg://user?id=42">x</a>'
    assert info.mention_markdown() == "[Bot](tg://user?id=42)"
    assert info.mention_markdown("x") == "[x](tg://user?id=42)"


def test_bot_full_info_decodes_pre_10_5_get_me():
    # A getMe result of a Bot API server older than 10.5 has neither of these fields.
    info = BotFullInfo.model_validate(
        {
            **dict.fromkeys(
                (
                    "can_join_groups",
                    "can_read_all_group_messages",
                    "supports_guest_queries",
                    "supports_inline_queries",
                    "can_connect_to_business",
                    "has_main_web_app",
                    "has_topics_enabled",
                    "allows_users_to_create_topics",
                    "can_manage_bots",
                    "supports_join_request_queries",
                ),
                False,
            ),
            "id": 1,
            "is_bot": True,
            "first_name": "Old",
            "username": "old_bot",
        }
    )
    assert info.needs_inline_query_location is None
    assert info.has_topic_sidebar is None
