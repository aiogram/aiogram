from aiogram.methods import GetMe
from aiogram.types import (
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
    async def test_me_is_user_built_from_get_me(self, bot: MockedBot):
        bot._me = None
        bot.add_result_for(GetMe, ok=True, result=bot_full_info(username="tbot", id=7))
        me = await bot.me()
        assert isinstance(me, User)
        assert (me.id, me.username, me.is_bot) == (7, "tbot", True)
