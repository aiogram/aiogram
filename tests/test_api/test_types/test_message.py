import datetime
from typing import Any, Dict, Type, Union, Optional

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
    SendPhoto,
    SendPoll,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVideoNote,
    SendVoice,
    CopyMessage,
    TelegramMethod,
)
from aiogram.types import (
    Animation,
    Audio,
    Chat,
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
    User,
    Venue,
    Video,
    VideoNote,
    Voice,
    MessageAutoDeleteTimerChanged,
    VoiceChatStarted,
    VoiceChatEnded,
    VoiceChatParticipantsInvited,
)
from aiogram.types.message import ContentType, Message

TEST_MESSAGE_TEXT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    text="test",
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_AUDIO = Message(
    message_id=42,
    date=datetime.datetime.now(),
    audio=Audio(file_id="file id", file_unique_id="file id", duration=42),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_ANIMATION = Message(
    message_id=42,
    date=datetime.datetime.now(),
    animation=Animation(
        file_id="file id", file_unique_id="file id", width=42, height=42, duration=0,
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_DOCUMENT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    document=Document(file_id="file id", file_unique_id="file id"),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_GAME = Message(
    message_id=42,
    date=datetime.datetime.now(),
    game=Game(
        title="title",
        description="description",
        photo=[PhotoSize(file_id="file id", file_unique_id="file id", width=42, height=42)],
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_PHOTO = Message(
    message_id=42,
    date=datetime.datetime.now(),
    photo=[PhotoSize(file_id="file id", file_unique_id="file id", width=42, height=42)],
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)

TEST_MESSAGE_STICKER = Message(
    message_id=42,
    date=datetime.datetime.now(),
    sticker=Sticker(
        file_id="file id", file_unique_id="file id", width=42, height=42, is_animated=False,
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_VIDEO = Message(
    message_id=42,
    date=datetime.datetime.now(),
    video=Video(file_id="file id", file_unique_id="file id", width=42, height=42, duration=0,),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_VIDEO_NOTE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    video_note=VideoNote(file_id="file id", file_unique_id="file id", length=0, duration=0),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_VOICE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    voice=Voice(file_id="file id", file_unique_id="file id", duration=0),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_CONTACT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    contact=Contact(phone_number="911", first_name="911"),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_VENUE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    venue=Venue(
        location=Location(latitude=3.14, longitude=3.14),
        title="Cupboard Under the Stairs",
        address="Under the stairs, 4 Privet Drive, "
        "Little Whinging, Surrey, England, Great Britain",
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_LOCATION = Message(
    message_id=42,
    date=datetime.datetime.now(),
    location=Location(longitude=3.14, latitude=3.14),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_NEW_CHAT_MEMBERS = Message(
    message_id=42,
    date=datetime.datetime.now(),
    new_chat_members=[User(id=42, is_bot=False, first_name="Test")],
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_LEFT_CHAT_MEMBER = Message(
    message_id=42,
    date=datetime.datetime.now(),
    left_chat_member=User(id=42, is_bot=False, first_name="Test"),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_INVOICE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    invoice=Invoice(
        title="test",
        description="test",
        start_parameter="brilliant",
        currency="BTC",
        total_amount=1,
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_SUCCESSFUL_PAYMENT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    successful_payment=SuccessfulPayment(
        currency="BTC",
        total_amount=42,
        invoice_payload="payload",
        telegram_payment_charge_id="charge",
        provider_payment_charge_id="payment",
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_CONNECTED_WEBSITE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    connected_website="token",
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_MIGRATE_FROM_CHAT_ID = Message(
    message_id=42,
    date=datetime.datetime.now(),
    migrate_from_chat_id=42,
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_MIGRATE_TO_CHAT_ID = Message(
    message_id=42,
    date=datetime.datetime.now(),
    migrate_to_chat_id=42,
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_PINNED_MESSAGE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    pinned_message=Message(
        message_id=42,
        date=datetime.datetime.now(),
        text="pinned",
        chat=Chat(id=42, type="private"),
        from_user=User(id=42, is_bot=False, first_name="Test"),
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_NEW_CHAT_TITLE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    new_chat_title="test",
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_NEW_CHAT_PHOTO = Message(
    message_id=42,
    date=datetime.datetime.now(),
    new_chat_photo=[PhotoSize(file_id="file id", file_unique_id="file id", width=42, height=42)],
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_DELETE_CHAT_PHOTO = Message(
    message_id=42,
    date=datetime.datetime.now(),
    delete_chat_photo=True,
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_GROUP_CHAT_CREATED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    group_chat_created=True,
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_PASSPORT_DATA = Message(
    message_id=42,
    date=datetime.datetime.now(),
    passport_data=PassportData(
        data=[], credentials=EncryptedCredentials(data="test", hash="test", secret="test"),
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_POLL = Message(
    message_id=42,
    date=datetime.datetime.now(),
    poll=Poll(
        id="QA",
        question="Q",
        options=[PollOption(text="A", voter_count=0), PollOption(text="B", voter_count=0),],
        is_closed=False,
        is_anonymous=False,
        type="quiz",
        allows_multiple_answers=False,
        total_voter_count=0,
        correct_option_id=1,
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_MESSAGE_AUTO_DELETE_TIMER_CHANGED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    message_auto_delete_timer_changed=MessageAutoDeleteTimerChanged(message_auto_delete_time=42),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_VOICE_CHAT_STARTED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    voice_chat_started=VoiceChatStarted(),
)
TEST_MESSAGE_VOICE_CHAT_ENDED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    voice_chat_ended=VoiceChatEnded(duration=42),
)
TEST_MESSAGE_VOICE_CHAT_PARTICIPANTS_INVITED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    voice_chat_participants_invited=VoiceChatParticipantsInvited(
        users=[User(id=69, is_bot=False, first_name="Test")]
    ),
)
TEST_MESSAGE_DICE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    dice=Dice(value=6, emoji="X"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_UNKNOWN = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)


class TestMessage:
    @pytest.mark.parametrize(
        "message,content_type",
        [
            [TEST_MESSAGE_TEXT, ContentType.TEXT],
            [TEST_MESSAGE_AUDIO, ContentType.AUDIO],
            [TEST_MESSAGE_ANIMATION, ContentType.ANIMATION],
            [TEST_MESSAGE_DOCUMENT, ContentType.DOCUMENT],
            [TEST_MESSAGE_GAME, ContentType.GAME],
            [TEST_MESSAGE_PHOTO, ContentType.PHOTO],
            [TEST_MESSAGE_STICKER, ContentType.STICKER],
            [TEST_MESSAGE_VIDEO, ContentType.VIDEO],
            [TEST_MESSAGE_VIDEO_NOTE, ContentType.VIDEO_NOTE],
            [TEST_MESSAGE_VOICE, ContentType.VOICE],
            [TEST_MESSAGE_CONTACT, ContentType.CONTACT],
            [TEST_MESSAGE_VENUE, ContentType.VENUE],
            [TEST_MESSAGE_LOCATION, ContentType.LOCATION],
            [TEST_MESSAGE_NEW_CHAT_MEMBERS, ContentType.NEW_CHAT_MEMBERS],
            [TEST_MESSAGE_LEFT_CHAT_MEMBER, ContentType.LEFT_CHAT_MEMBER],
            [TEST_MESSAGE_INVOICE, ContentType.INVOICE],
            [TEST_MESSAGE_SUCCESSFUL_PAYMENT, ContentType.SUCCESSFUL_PAYMENT],
            [TEST_MESSAGE_CONNECTED_WEBSITE, ContentType.CONNECTED_WEBSITE],
            [TEST_MESSAGE_MIGRATE_FROM_CHAT_ID, ContentType.MIGRATE_FROM_CHAT_ID],
            [TEST_MESSAGE_MIGRATE_TO_CHAT_ID, ContentType.MIGRATE_TO_CHAT_ID],
            [TEST_MESSAGE_PINNED_MESSAGE, ContentType.PINNED_MESSAGE],
            [TEST_MESSAGE_NEW_CHAT_TITLE, ContentType.NEW_CHAT_TITLE],
            [TEST_MESSAGE_NEW_CHAT_PHOTO, ContentType.NEW_CHAT_PHOTO],
            [TEST_MESSAGE_DELETE_CHAT_PHOTO, ContentType.DELETE_CHAT_PHOTO],
            [TEST_MESSAGE_GROUP_CHAT_CREATED, ContentType.GROUP_CHAT_CREATED],
            [TEST_MESSAGE_PASSPORT_DATA, ContentType.PASSPORT_DATA],
            [TEST_MESSAGE_POLL, ContentType.POLL],
            [
                TEST_MESSAGE_MESSAGE_AUTO_DELETE_TIMER_CHANGED,
                ContentType.MESSAGE_AUTO_DELETE_TIMER_CHANGED,
            ],
            [TEST_MESSAGE_VOICE_CHAT_STARTED, ContentType.VOICE_CHAT_STARTED],
            [TEST_MESSAGE_VOICE_CHAT_ENDED, ContentType.VOICE_CHAT_ENDED],
            [
                TEST_MESSAGE_VOICE_CHAT_PARTICIPANTS_INVITED,
                ContentType.VOICE_CHAT_PARTICIPANTS_INVITED,
            ],
            [TEST_MESSAGE_DICE, ContentType.DICE],
            [TEST_MESSAGE_UNKNOWN, ContentType.UNKNOWN],
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
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
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

    def test_copy_to(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.copy_to(chat_id=message.chat.id)
        assert isinstance(method, CopyMessage)
        assert method.chat_id == message.chat.id

    @pytest.mark.parametrize(
        "message,expected_method",
        [
            [TEST_MESSAGE_TEXT, SendMessage],
            [TEST_MESSAGE_AUDIO, SendAudio],
            [TEST_MESSAGE_ANIMATION, SendAnimation],
            [TEST_MESSAGE_DOCUMENT, SendDocument],
            [TEST_MESSAGE_GAME, None],
            [TEST_MESSAGE_PHOTO, SendPhoto],
            [TEST_MESSAGE_STICKER, SendSticker],
            [TEST_MESSAGE_VIDEO, SendVideo],
            [TEST_MESSAGE_VIDEO_NOTE, SendVideoNote],
            [TEST_MESSAGE_VOICE, SendVoice],
            [TEST_MESSAGE_CONTACT, SendContact],
            [TEST_MESSAGE_VENUE, SendVenue],
            [TEST_MESSAGE_LOCATION, SendLocation],
            [TEST_MESSAGE_NEW_CHAT_MEMBERS, None],
            [TEST_MESSAGE_LEFT_CHAT_MEMBER, None],
            [TEST_MESSAGE_INVOICE, None],
            [TEST_MESSAGE_SUCCESSFUL_PAYMENT, None],
            [TEST_MESSAGE_CONNECTED_WEBSITE, None],
            [TEST_MESSAGE_MIGRATE_FROM_CHAT_ID, None],
            [TEST_MESSAGE_MIGRATE_TO_CHAT_ID, None],
            [TEST_MESSAGE_PINNED_MESSAGE, None],
            [TEST_MESSAGE_NEW_CHAT_TITLE, None],
            [TEST_MESSAGE_NEW_CHAT_PHOTO, None],
            [TEST_MESSAGE_DELETE_CHAT_PHOTO, None],
            [TEST_MESSAGE_GROUP_CHAT_CREATED, None],
            [TEST_MESSAGE_PASSPORT_DATA, None],
            [TEST_MESSAGE_POLL, SendPoll],
            [TEST_MESSAGE_MESSAGE_AUTO_DELETE_TIMER_CHANGED, None],
            [TEST_MESSAGE_VOICE_CHAT_STARTED, None],
            [TEST_MESSAGE_VOICE_CHAT_ENDED, None],
            [TEST_MESSAGE_VOICE_CHAT_PARTICIPANTS_INVITED, None],
            [TEST_MESSAGE_DICE, SendDice],
            [TEST_MESSAGE_UNKNOWN, None],
        ],
    )
    def test_send_copy(
        self, message: Message, expected_method: Optional[Type[TelegramMethod]],
    ):
        if expected_method is None:
            with pytest.raises(TypeError, match="This type of message can't be copied."):
                message.send_copy(chat_id=42)
            return

        method = message.send_copy(chat_id=42)
        if method:
            assert isinstance(method, expected_method)
        # TODO: Check additional fields
