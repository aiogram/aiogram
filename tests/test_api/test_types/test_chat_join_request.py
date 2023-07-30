import datetime
from typing import Any, Dict, Type, Union

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
            ["answer_animation", dict(animation="animation"), SendAnimation],
            ["answer_audio", dict(audio="audio"), SendAudio],
            ["answer_contact", dict(phone_number="+000000000000", first_name="Test"), SendContact],
            ["answer_document", dict(document="document"), SendDocument],
            ["answer_game", dict(game_short_name="game"), SendGame],
            [
                "answer_invoice",
                dict(
                    title="title",
                    description="description",
                    payload="payload",
                    provider_token="provider_token",
                    start_parameter="start_parameter",
                    currency="currency",
                    prices=[],
                ),
                SendInvoice,
            ],
            ["answer_location", dict(latitude=0.42, longitude=0.42), SendLocation],
            ["answer_media_group", dict(media=[]), SendMediaGroup],
            ["answer", dict(text="test"), SendMessage],
            ["answer_photo", dict(photo="photo"), SendPhoto],
            ["answer_poll", dict(question="Q?", options=[]), SendPoll],
            ["answer_dice", dict(), SendDice],
            ["answer_sticker", dict(sticker="sticker"), SendSticker],
            ["answer_sticker", dict(sticker="sticker"), SendSticker],
            [
                "answer_venue",
                dict(
                    latitude=0.42,
                    longitude=0.42,
                    title="title",
                    address="address",
                ),
                SendVenue,
            ],
            ["answer_video", dict(video="video"), SendVideo],
            ["answer_video_note", dict(video_note="video_note"), SendVideoNote],
            ["answer_voice", dict(voice="voice"), SendVoice],
        ],
    )
    @pytest.mark.parametrize("suffix", ["", "_pm"])
    def test_answer_aliases(
        self,
        alias_for_method: str,
        suffix: str,
        kwargs: Dict[str, Any],
        method_class: Type[
            Union[
                SendAnimation,
                SendAudio,
                SendContact,
                SendDocument,
                SendGame,
                SendInvoice,
                SendLocation,
                SendMediaGroup,
                SendMessage,
                SendPhoto,
                SendPoll,
                SendSticker,
                SendSticker,
                SendVenue,
                SendVideo,
                SendVideoNote,
                SendVoice,
            ]
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
