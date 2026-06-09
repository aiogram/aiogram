import datetime
from typing import Any

import pytest

from aiogram.methods import (
    ApproveChatJoinRequest,
    DeclineChatJoinRequest,
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
    SendPhoto,
    SendPoll,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVideoNote,
    SendVoice,
)
from aiogram.types import Chat, ChatJoinRequest, User


class TestChatJoinRequest:
    def test_approve_alias(self):
        chat_join_request = ChatJoinRequest(
            chat=Chat(id=-42, type="supergroup"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            user_chat_id=42,
            date=datetime.datetime.now(),
        )

        api_method = chat_join_request.approve()

        assert isinstance(api_method, ApproveChatJoinRequest)
        assert api_method.chat_id == chat_join_request.chat.id
        assert api_method.user_id == chat_join_request.from_user.id

    def test_decline_alias(self):
        chat_join_request = ChatJoinRequest(
            chat=Chat(id=-42, type="supergroup"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            user_chat_id=42,
            date=datetime.datetime.now(),
        )

        api_method = chat_join_request.decline()

        assert isinstance(api_method, DeclineChatJoinRequest)
        assert api_method.chat_id == chat_join_request.chat.id
        assert api_method.user_id == chat_join_request.from_user.id

    @pytest.mark.parametrize(
        "alias_for_method,kwargs,method_class",
        [
            ["answer_animation", {"animation": "animation"}, SendAnimation],
            ["answer_audio", {"audio": "audio"}, SendAudio],
            [
                "answer_contact",
                {"phone_number": "+000000000000", "first_name": "Test"},
                SendContact,
            ],
            ["answer_document", {"document": "document"}, SendDocument],
            ["answer_game", {"game_short_name": "game"}, SendGame],
            [
                "answer_invoice",
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
            ["answer_location", {"latitude": 0.42, "longitude": 0.42}, SendLocation],
            ["answer_media_group", {"media": []}, SendMediaGroup],
            ["answer", {"text": "test"}, SendMessage],
            ["answer_photo", {"photo": "photo"}, SendPhoto],
            ["answer_poll", {"question": "Q?", "options": []}, SendPoll],
            ["answer_dice", {}, SendDice],
            ["answer_sticker", {"sticker": "sticker"}, SendSticker],
            ["answer_sticker", {"sticker": "sticker"}, SendSticker],
            [
                "answer_venue",
                {
                    "latitude": 0.42,
                    "longitude": 0.42,
                    "title": "title",
                    "address": "address",
                },
                SendVenue,
            ],
            ["answer_video", {"video": "video"}, SendVideo],
            ["answer_video_note", {"video_note": "video_note"}, SendVideoNote],
            ["answer_voice", {"voice": "voice"}, SendVoice],
        ],
    )
    @pytest.mark.parametrize("suffix", ["", "_pm"])
    def test_answer_aliases(
        self,
        alias_for_method: str,
        suffix: str,
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
        ],
    ):
        event = ChatJoinRequest(
            chat=Chat(id=-42, type="channel"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            user_chat_id=42,
            date=datetime.datetime.now(),
        )

        alias = getattr(event, alias_for_method + suffix)
        assert callable(alias)

        api_method = alias(**kwargs)
        assert isinstance(api_method, method_class)

        if suffix == "_pm":
            assert api_method.chat_id == event.user_chat_id
        else:
            assert api_method.chat_id == event.chat.id

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value
