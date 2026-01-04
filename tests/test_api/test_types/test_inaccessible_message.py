from typing import Any

import pytest

from aiogram.methods import (
    SendAnimation,
    SendAudio,
    SendContact,
    SendDice,
    SendDocument,
    SendGame,
    SendInvoice,
    SendLocation,
    SendMediaGroup,
    SendMessage,
    SendPaidMedia,
    SendPhoto,
    SendPoll,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVideoNote,
    SendVoice,
)
from aiogram.types import Chat
from aiogram.types.inaccessible_message import InaccessibleMessage
from aiogram.types.message import ContentType

TEST_MESSAGE_UNKNOWN = InaccessibleMessage(
    message_id=42,
    chat=Chat(id=42, type="private"),
)

MESSAGES_AND_CONTENT_TYPES = [
    [TEST_MESSAGE_UNKNOWN, ContentType.UNKNOWN],
]


class TestMessage:
    @pytest.mark.parametrize(
        "message,content_type",
        MESSAGES_AND_CONTENT_TYPES,
    )
    def test_as_reply_parameters(self, message, content_type):
        reply_parameters = message.as_reply_parameters()
        assert reply_parameters.message_id == message.message_id
        assert reply_parameters.chat_id == message.chat.id

    @pytest.mark.parametrize(
        "alias_for_method,kwargs,method_class",
        [
            ["animation", {"animation": "animation"}, SendAnimation],
            ["audio", {"audio": "audio"}, SendAudio],
            ["contact", {"phone_number": "+000000000000", "first_name": "Test"}, SendContact],
            ["document", {"document": "document"}, SendDocument],
            ["game", {"game_short_name": "game"}, SendGame],
            [
                "invoice",
                {
                    "title": "title",
                    "description": "description",
                    "payload": "payload",
                    "provider_token": "provider_token",
                    "start_parameter": "start_parameter",
                    "currency": "currency",
                    "prices": [],
                },
                SendInvoice,
            ],
            ["location", {"latitude": 0.42, "longitude": 0.42}, SendLocation],
            ["media_group", {"media": []}, SendMediaGroup],
            ["", {"text": "test"}, SendMessage],
            ["photo", {"photo": "photo"}, SendPhoto],
            ["poll", {"question": "Q?", "options": []}, SendPoll],
            ["dice", {}, SendDice],
            ["sticker", {"sticker": "sticker"}, SendSticker],
            ["sticker", {"sticker": "sticker"}, SendSticker],
            [
                "venue",
                {
                    "latitude": 0.42,
                    "longitude": 0.42,
                    "title": "title",
                    "address": "address",
                },
                SendVenue,
            ],
            ["video", {"video": "video"}, SendVideo],
            ["video_note", {"video_note": "video_note"}, SendVideoNote],
            ["voice", {"voice": "voice"}, SendVoice],
            ["paid_media", {"media": [], "star_count": 42}, SendPaidMedia],
        ],
    )
    @pytest.mark.parametrize("alias_type", ["reply", "answer"])
    def test_reply_answer_aliases(
        self,
        alias_for_method: str,
        alias_type: str,
        kwargs: dict[str, Any],
        method_class: type[
            SendAnimation
            | SendAudio
            | SendContact
            | SendDocument
            | SendGame
            | SendInvoice
            | SendLocation
            | SendMediaGroup
            | SendMessage
            | SendPhoto
            | SendPoll
            | SendSticker
            | SendSticker
            | SendVenue
            | SendVideo
            | SendVideoNote
            | SendVoice
            | SendPaidMedia
        ],
    ):
        message = InaccessibleMessage(
            message_id=42,
            chat=Chat(id=42, type="private"),
        )
        alias_name = "_".join(item for item in [alias_type, alias_for_method] if item)

        alias = getattr(message, alias_name)
        assert callable(alias)

        api_method = alias(**kwargs)
        assert isinstance(api_method, method_class)

        assert api_method.chat_id == message.chat.id
        if alias_type == "reply":
            assert api_method.reply_parameters
            assert api_method.reply_parameters.message_id == message.message_id
            assert api_method.reply_parameters.chat_id == message.chat.id
        else:
            assert api_method.reply_parameters is None

        if hasattr(api_method, "reply_parameters"):
            if alias_type == "reply":
                assert api_method.reply_parameters is not None
                assert api_method.reply_parameters.message_id == message.message_id
                assert api_method.reply_parameters.chat_id == message.chat.id
            else:
                assert api_method.reply_parameters is None

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value
