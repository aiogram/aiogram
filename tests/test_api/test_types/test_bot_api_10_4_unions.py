"""Discriminated unions introduced in Bot API 10.4 resolve to concrete members."""

import pytest
from pydantic import ValidationError

from aiogram.types import (
    ChatFullInfo,
    ChatShareThemeEmoji,
    ChatShareThemeUniqueGift,
    EmojiTypeCustomEmoji,
    EmojiTypeEmoji,
    RichBlockParagraph,
    RichTextBold,
    RichTextTonAddress,
    SharedWidgetQuery,
    UniqueGift,
    WidgetQuery,
    WidgetQueryTypeData,
    WidgetQueryTypeSentTransaction,
    WidgetQueryTypeSignData,
)

STICKER = {
    "file_id": "file_id",
    "file_unique_id": "file_unique_id",
    "type": "regular",
    "width": 512,
    "height": 512,
    "is_animated": False,
    "is_video": False,
}
UNIQUE_GIFT = {
    "gift_id": "gift_id",
    "base_name": "gift",
    "name": "gift-1",
    "number": 1,
    "model": {"name": "model", "sticker": STICKER, "rarity_per_mille": 100},
    "symbol": {"name": "symbol", "sticker": STICKER, "rarity_per_mille": 100},
    "backdrop": {
        "name": "backdrop",
        "colors": {"center_color": 1, "edge_color": 2, "symbol_color": 3, "text_color": 4},
        "rarity_per_mille": 100,
    },
}
WALLET = {"address": "EQ_address", "amount": "100"}
USER = {"id": 42, "is_bot": False, "first_name": "Test"}


class TestWidgetQueryTypeUnion:
    @pytest.mark.parametrize(
        "query_type,expected",
        [
            [{"type": "data"}, WidgetQueryTypeData],
            [{"type": "sign_data", "wallet": WALLET, "sign_data": "x"}, WidgetQueryTypeSignData],
            [
                {"type": "sent_transaction", "wallet": WALLET, "msg_hash": "x"},
                WidgetQueryTypeSentTransaction,
            ],
        ],
    )
    def test_resolves_concrete_type(self, query_type: dict, expected: type):
        widget_query = WidgetQuery.model_validate(
            {
                "id": "id",
                "from": USER,
                "chat_instance": "instance",
                "type": query_type,
                "data": "data",
            }
        )
        shared_widget_query = SharedWidgetQuery.model_validate(
            {"id": "id", "from": USER, "type": query_type, "data": "data", "widget_id": "w"}
        )

        assert type(widget_query.type) is expected
        assert type(shared_widget_query.type) is expected

    def test_unknown_tag(self):
        with pytest.raises(ValidationError) as exc_info:
            SharedWidgetQuery.model_validate(
                {"id": "id", "from": USER, "type": {"type": "nope"}, "data": "", "widget_id": "w"}
            )

        assert exc_info.value.errors()[0]["type"] == "union_tag_invalid"


class TestChatShareThemeUnion:
    def test_emoji_theme(self):
        chat = ChatFullInfo.model_validate(
            {
                "id": 42,
                "type": "private",
                "accent_color_id": 0,
                "max_reaction_count": 0,
                "accepted_gift_types": {
                    "unlimited_gifts": True,
                    "limited_gifts": True,
                    "unique_gifts": True,
                    "premium_subscription": True,
                    "gifts_from_channels": True,
                },
                "share_theme": {
                    "type": "emoji",
                    "emojis": [
                        {"type": "emoji", "emoji": "🔥"},
                        {"type": "custom_emoji", "custom_emoji_id": "42"},
                    ],
                },
            }
        )

        assert isinstance(chat.share_theme, ChatShareThemeEmoji)
        emoji, custom_emoji = chat.share_theme.emojis
        assert isinstance(emoji, EmojiTypeEmoji)
        assert isinstance(custom_emoji, EmojiTypeCustomEmoji)

    def test_unique_gift_theme(self):
        theme = ChatShareThemeUniqueGift.model_validate(
            {"type": "unique_gift", "gift": UNIQUE_GIFT}
        )
        assert isinstance(theme.gift, UniqueGift)

    def test_unknown_emoji_tag(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatShareThemeEmoji.model_validate({"emojis": [{"type": "nope"}]})

        assert exc_info.value.errors()[0]["type"] == "union_tag_invalid"


class TestRichTextTonAddress:
    def test_resolves_concrete_type(self):
        paragraph = RichBlockParagraph.model_validate(
            {
                "type": "paragraph",
                "text": {
                    "type": "ton_address",
                    "address": "EQ_address",
                    "text": {"type": "bold", "text": "wallet"},
                },
            }
        )

        assert isinstance(paragraph.text, RichTextTonAddress)
        assert paragraph.text.address == "EQ_address"
        assert isinstance(paragraph.text.text, RichTextBold)
