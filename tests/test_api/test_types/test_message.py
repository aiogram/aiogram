import datetime
from typing import Any, Dict, Type, Union

import pytest

from aiogram.api.methods import (
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
from aiogram.api.types import (
    Animation,
    Audio,
    Contact,
    Dice,
    Document,
    EncryptedCredentials,
    Game,
    Invoice,
    Location,
    PassportData,
    PhotoSize,
    Poll,
    PollOption,
    Sticker,
    SuccessfulPayment,
    Venue,
    Video,
    VideoNote,
    Voice,
)
from aiogram.api.types.message import ContentType, Message
from tests.factories.chat import ChatFactory
from tests.factories.message import MessageFactory
from tests.factories.user import UserFactory


class TestMessage:
    @pytest.mark.parametrize(
        "message,content_type",
        [
            [
                MessageFactory(
                ),
                ContentType.TEXT,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    audio=Audio(file_id="file id", file_unique_id="file id", duration=42),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.AUDIO,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    animation=Animation(
                        file_id="file id",
                        file_unique_id="file id",
                        width=42,
                        height=42,
                        duration=0,
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.ANIMATION,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    document=Document(file_id="file id", file_unique_id="file id"),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.DOCUMENT,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    game=Game(
                        title="title",
                        description="description",
                        photo=[
                            PhotoSize(
                                file_id="file id", file_unique_id="file id", width=42, height=42
                            )
                        ],
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.GAME,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    photo=[
                        PhotoSize(file_id="file id", file_unique_id="file id", width=42, height=42)
                    ],
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.PHOTO,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    sticker=Sticker(
                        file_id="file id",
                        file_unique_id="file id",
                        width=42,
                        height=42,
                        is_animated=False,
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.STICKER,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    video=Video(
                        file_id="file id",
                        file_unique_id="file id",
                        width=42,
                        height=42,
                        duration=0,
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.VIDEO,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    video_note=VideoNote(
                        file_id="file id", file_unique_id="file id", length=0, duration=0
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.VIDEO_NOTE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    voice=Voice(file_id="file id", file_unique_id="file id", duration=0),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.VOICE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    contact=Contact(phone_number="911", first_name="911"),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.CONTACT,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    venue=Venue(
                        location=Location(latitude=3.14, longitude=3.14),
                        title="Cupboard Under the Stairs",
                        address="Under the stairs, 4 Privet Drive, "
                        "Little Whinging, Surrey, England, Great Britain",
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.VENUE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    location=Location(longitude=3.14, latitude=3.14),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.LOCATION,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    new_chat_members=[UserFactory()],
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.NEW_CHAT_MEMBERS,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    left_chat_member=UserFactory(),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.LEFT_CHAT_MEMBER,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    invoice=Invoice(
                        title="test",
                        description="test",
                        start_parameter="brilliant",
                        currency="BTC",
                        total_amount=1,
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.INVOICE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    successful_payment=SuccessfulPayment(
                        currency="BTC",
                        total_amount=42,
                        invoice_payload="payload",
                        telegram_payment_charge_id="charge",
                        provider_payment_charge_id="payment",
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.SUCCESSFUL_PAYMENT,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    connected_website="token",
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.CONNECTED_WEBSITE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    migrate_from_chat_id=42,
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.MIGRATE_FROM_CHAT_ID,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    migrate_to_chat_id=42,
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.MIGRATE_TO_CHAT_ID,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    pinned_message=Message(
                        message_id=42,
                        date=datetime.datetime.now(),
                        text="pinned",
                        chat=ChatFactory(),
                        from_user=UserFactory(),
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.PINNED_MESSAGE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    new_chat_title="test",
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.NEW_CHAT_TITLE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    new_chat_photo=[
                        PhotoSize(file_id="file id", file_unique_id="file id", width=42, height=42)
                    ],
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.NEW_CHAT_PHOTO,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    delete_chat_photo=True,
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.DELETE_CHAT_PHOTO,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    group_chat_created=True,
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.GROUP_CHAT_CREATED,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    passport_data=PassportData(
                        data=[],
                        credentials=EncryptedCredentials(data="test", hash="test", secret="test"),
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.PASSPORT_DATA,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    poll=Poll(
                        id="QA",
                        question="Q",
                        options=[
                            PollOption(text="A", voter_count=0),
                            PollOption(text="B", voter_count=0),
                        ],
                        is_closed=False,
                        is_anonymous=False,
                        type="quiz",
                        allows_multiple_answers=False,
                        total_voter_count=0,
                        correct_option_id=1,
                    ),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.POLL,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    chat=ChatFactory(),
                    dice=Dice(value=6, emoji="X"),
                    from_user=UserFactory(),
                ),
                ContentType.DICE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    chat=ChatFactory(),
                    from_user=UserFactory(),
                ),
                ContentType.UNKNOWN,
            ],
        ],
    )
    def test_content_type(self, message: Message, content_type: str):
        assert message.content_type == content_type

    @pytest.mark.parametrize(
        "alias_for_method,kwargs,method_class",
        [
            ["animation", dict(animation="animation"), SendAnimation],
            ["audio", dict(audio="audio"), SendAudio],
            ["contact", dict(phone_number="+000000000000", first_name="Test"), SendContact],
            ["document", dict(document="document"), SendDocument],
            ["game", dict(game_short_name="game"), SendGame],
            [
                "invoice",
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
            ["location", dict(latitude=0.42, longitude=0.42), SendLocation],
            ["media_group", dict(media=[]), SendMediaGroup],
            ["", dict(text="test"), SendMessage],
            ["photo", dict(photo="photo"), SendPhoto],
            ["poll", dict(question="Q?", options=[]), SendPoll],
            ["dice", dict(), SendDice],
            ["sticker", dict(sticker="sticker"), SendSticker],
            ["sticker", dict(sticker="sticker"), SendSticker],
            [
                "venue",
                dict(latitude=0.42, longitude=0.42, title="title", address="address",),
                SendVenue,
            ],
            ["video", dict(video="video"), SendVideo],
            ["video_note", dict(video_note="video_note"), SendVideoNote],
            ["voice", dict(voice="voice"), SendVoice],
        ],
    )
    @pytest.mark.parametrize("alias_type", ["reply", "answer"])
    def test_reply_answer_aliases(
        self,
        alias_for_method: str,
        alias_type: str,
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
        message = Message(message_id=42, chat=ChatFactory(), date=datetime.datetime.now())
        alias_name = "_".join(item for item in [alias_type, alias_for_method] if item)

        alias = getattr(message, alias_name)
        assert callable(alias)

        api_method = alias(**kwargs)
        assert isinstance(api_method, method_class)

        assert api_method.chat_id == message.chat.id
        if alias_type == "reply":
            assert api_method.reply_to_message_id == message.message_id
        else:
            assert api_method.reply_to_message_id is None

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value
