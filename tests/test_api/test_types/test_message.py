import datetime
from typing import Any, Dict, Optional, Type, Union

import pytest

from aiogram.enums import ParseMode
from aiogram.methods import (
    CopyMessage,
    DeleteMessage,
    EditMessageCaption,
    EditMessageLiveLocation,
    EditMessageMedia,
    EditMessageReplyMarkup,
    EditMessageText,
    ForwardMessage,
    PinChatMessage,
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
    StopMessageLiveLocation,
    TelegramMethod,
    UnpinChatMessage,
)
from aiogram.types import (
    UNSET_PARSE_MODE,
    Animation,
    Audio,
    Chat,
    ChatShared,
    Contact,
    Dice,
    Document,
    EncryptedCredentials,
    ForumTopicClosed,
    ForumTopicCreated,
    ForumTopicEdited,
    ForumTopicReopened,
    Game,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Invoice,
    Location,
    MessageAutoDeleteTimerChanged,
    MessageEntity,
    PassportData,
    PhotoSize,
    Poll,
    PollOption,
    ProximityAlertTriggered,
    Sticker,
    Story,
    SuccessfulPayment,
    User,
    UserShared,
    Venue,
    Video,
    VideoChatEnded,
    VideoChatParticipantsInvited,
    VideoChatScheduled,
    VideoChatStarted,
    VideoNote,
    Voice,
    WebAppData,
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
        file_id="file id",
        file_unique_id="file id",
        width=42,
        height=42,
        duration=0,
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
        file_id="file id",
        file_unique_id="file id",
        width=42,
        height=42,
        is_animated=False,
        is_video=False,
        type="regular",
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_VIDEO = Message(
    message_id=42,
    date=datetime.datetime.now(),
    video=Video(
        file_id="file id",
        file_unique_id="file id",
        width=42,
        height=42,
        duration=0,
    ),
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
TEST_MESSAGE_SUPERGROUP_CHAT_CREATED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    supergroup_chat_created=True,
    chat=Chat(id=-10042, type="supergroup"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_CHANNEL_CHAT_CREATED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    channel_chat_created=True,
    chat=Chat(id=-10042, type="channel"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_PASSPORT_DATA = Message(
    message_id=42,
    date=datetime.datetime.now(),
    passport_data=PassportData(
        data=[],
        credentials=EncryptedCredentials(data="test", hash="test", secret="test"),
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_PROXIMITY_ALERT_TRIGGERED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="supergroup"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    proximity_alert_triggered=ProximityAlertTriggered(
        traveler=User(id=1, is_bot=False, first_name="Traveler"),
        watcher=User(id=2, is_bot=False, first_name="Watcher"),
        distance=42,
    ),
)
TEST_MESSAGE_POLL = Message(
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
TEST_MESSAGE_VIDEO_CHAT_STARTED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    video_chat_started=VideoChatStarted(),
)
TEST_MESSAGE_VIDEO_CHAT_ENDED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    video_chat_ended=VideoChatEnded(duration=42),
)
TEST_MESSAGE_VIDEO_CHAT_PARTICIPANTS_INVITED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    video_chat_participants_invited=VideoChatParticipantsInvited(
        users=[User(id=69, is_bot=False, first_name="Test")]
    ),
)
TEST_MESSAGE_VIDEO_CHAT_SCHEDULED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    video_chat_scheduled=VideoChatScheduled(
        start_date=datetime.datetime.now(),
    ),
)
TEST_MESSAGE_DICE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    dice=Dice(value=6, emoji="X"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_WEB_APP_DATA = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    web_app_data=WebAppData(data="test", button_text="Test"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_FORUM_TOPIC_CREATED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    forum_topic_created=ForumTopicCreated(
        name="test",
        icon_color=0xFFD67E,
    ),
)
TEST_FORUM_TOPIC_EDITED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    forum_topic_edited=ForumTopicEdited(
        name="test_edited",
        icon_color=0xFFD67E,
    ),
)
TEST_FORUM_TOPIC_CLOSED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    forum_topic_closed=ForumTopicClosed(),
)
TEST_FORUM_TOPIC_REOPENED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    forum_topic_reopened=ForumTopicReopened(),
)
TEST_USER_SHARED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    user_shared=UserShared(request_id=42, user_id=42),
)
TEST_CHAT_SHARED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    chat_shared=ChatShared(request_id=42, chat_id=42),
)
TEST_MESSAGE_STORY = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    story=Story(),
    forward_signature="Test",
    forward_date=datetime.datetime.now(),
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
            [TEST_MESSAGE_SUPERGROUP_CHAT_CREATED, ContentType.SUPERGROUP_CHAT_CREATED],
            [TEST_MESSAGE_CHANNEL_CHAT_CREATED, ContentType.CHANNEL_CHAT_CREATED],
            [TEST_MESSAGE_PASSPORT_DATA, ContentType.PASSPORT_DATA],
            [TEST_MESSAGE_PROXIMITY_ALERT_TRIGGERED, ContentType.PROXIMITY_ALERT_TRIGGERED],
            [TEST_MESSAGE_POLL, ContentType.POLL],
            [
                TEST_MESSAGE_MESSAGE_AUTO_DELETE_TIMER_CHANGED,
                ContentType.MESSAGE_AUTO_DELETE_TIMER_CHANGED,
            ],
            [TEST_MESSAGE_VIDEO_CHAT_SCHEDULED, ContentType.VIDEO_CHAT_SCHEDULED],
            [TEST_MESSAGE_VIDEO_CHAT_STARTED, ContentType.VIDEO_CHAT_STARTED],
            [TEST_MESSAGE_VIDEO_CHAT_ENDED, ContentType.VIDEO_CHAT_ENDED],
            [
                TEST_MESSAGE_VIDEO_CHAT_PARTICIPANTS_INVITED,
                ContentType.VIDEO_CHAT_PARTICIPANTS_INVITED,
            ],
            [TEST_MESSAGE_DICE, ContentType.DICE],
            [TEST_MESSAGE_WEB_APP_DATA, ContentType.WEB_APP_DATA],
            [TEST_FORUM_TOPIC_CREATED, ContentType.FORUM_TOPIC_CREATED],
            [TEST_FORUM_TOPIC_EDITED, ContentType.FORUM_TOPIC_EDITED],
            [TEST_FORUM_TOPIC_CLOSED, ContentType.FORUM_TOPIC_CLOSED],
            [TEST_FORUM_TOPIC_REOPENED, ContentType.FORUM_TOPIC_REOPENED],
            [TEST_USER_SHARED, ContentType.USER_SHARED],
            [TEST_CHAT_SHARED, ContentType.CHAT_SHARED],
            [TEST_MESSAGE_STORY, ContentType.STORY],
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
                dict(
                    latitude=0.42,
                    longitude=0.42,
                    title="title",
                    address="address",
                ),
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
            [TEST_MESSAGE_STORY, ForwardMessage],
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
            [TEST_MESSAGE_SUPERGROUP_CHAT_CREATED, None],
            [TEST_MESSAGE_CHANNEL_CHAT_CREATED, None],
            [TEST_MESSAGE_PASSPORT_DATA, None],
            [TEST_MESSAGE_PROXIMITY_ALERT_TRIGGERED, None],
            [TEST_MESSAGE_POLL, SendPoll],
            [TEST_MESSAGE_MESSAGE_AUTO_DELETE_TIMER_CHANGED, None],
            [TEST_MESSAGE_VIDEO_CHAT_STARTED, None],
            [TEST_MESSAGE_VIDEO_CHAT_ENDED, None],
            [TEST_MESSAGE_VIDEO_CHAT_PARTICIPANTS_INVITED, None],
            [TEST_MESSAGE_DICE, SendDice],
            [TEST_USER_SHARED, None],
            [TEST_CHAT_SHARED, None],
            [TEST_MESSAGE_UNKNOWN, None],
        ],
    )
    def test_send_copy(
        self,
        message: Message,
        expected_method: Optional[Type[TelegramMethod]],
    ):
        if expected_method is None:
            with pytest.raises(TypeError, match="This type of message can't be copied."):
                message.send_copy(chat_id=42)
            return

        method = message.send_copy(chat_id=42)
        assert isinstance(method, expected_method)
        if hasattr(method, "parse_mode"):
            # default parse mode in send_copy
            assert method.parse_mode is None
        # TODO: Check additional fields

    @pytest.mark.parametrize(
        "custom_parse_mode",
        [
            UNSET_PARSE_MODE,
            *list(ParseMode),
        ],
    )
    @pytest.mark.parametrize(
        "message,expected_method",
        [
            [TEST_MESSAGE_TEXT, SendMessage],
            [TEST_MESSAGE_AUDIO, SendAudio],
            [TEST_MESSAGE_ANIMATION, SendAnimation],
            [TEST_MESSAGE_DOCUMENT, SendDocument],
            [TEST_MESSAGE_PHOTO, SendPhoto],
            [TEST_MESSAGE_VIDEO, SendVideo],
            [TEST_MESSAGE_VOICE, SendVoice],
        ],
    )
    def test_send_copy_custom_parse_mode(
        self,
        message: Message,
        expected_method: Optional[Type[TelegramMethod]],
        custom_parse_mode: Optional[str],
    ):
        method = message.send_copy(
            chat_id=42,
            parse_mode=custom_parse_mode,
        )
        assert isinstance(method, expected_method)
        assert method.parse_mode == custom_parse_mode

    def test_edit_text(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.edit_text(text="test")
        assert isinstance(method, EditMessageText)
        assert method.chat_id == message.chat.id

    def test_forward(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.forward(chat_id=69)
        assert isinstance(method, ForwardMessage)
        assert method.chat_id == 69
        assert method.from_chat_id == message.chat.id

    def test_edit_media(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.edit_media(media=InputMediaPhoto(media="photo.jpg"))
        assert isinstance(method, EditMessageMedia)
        assert method.chat_id == message.chat.id

    def test_edit_reply_markup(self):
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="test",
                        callback_data="test",
                    ),
                ],
            ]
        )
        reply_markup_new = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="test2",
                        callback_data="test2",
                    ),
                ],
            ]
        )

        message = Message(
            message_id=42,
            chat=Chat(id=42, type="private"),
            date=datetime.datetime.now(),
            reply_markup=reply_markup,
        )
        method = message.edit_reply_markup(
            reply_markup=reply_markup_new,
        )
        assert isinstance(method, EditMessageReplyMarkup)
        assert method.reply_markup == reply_markup_new
        assert method.chat_id == message.chat.id

    def test_delete_reply_markup(self):
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="test",
                        callback_data="test",
                    ),
                ],
            ]
        )

        message = Message(
            message_id=42,
            chat=Chat(id=42, type="private"),
            date=datetime.datetime.now(),
            reply_markup=reply_markup,
        )
        method = message.delete_reply_markup()
        assert isinstance(method, EditMessageReplyMarkup)
        assert method.reply_markup is None
        assert method.chat_id == message.chat.id

    def test_edit_live_location(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.edit_live_location(latitude=42, longitude=69)
        assert isinstance(method, EditMessageLiveLocation)
        assert method.chat_id == message.chat.id

    def test_stop_live_location(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.stop_live_location()
        assert isinstance(method, StopMessageLiveLocation)
        assert method.chat_id == message.chat.id

    def test_edit_caption(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.edit_caption(caption="test")
        assert isinstance(method, EditMessageCaption)
        assert method.chat_id == message.chat.id

    def test_delete(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.delete()
        assert isinstance(method, DeleteMessage)
        assert method.chat_id == message.chat.id
        assert method.message_id == message.message_id

    def test_pin(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.pin()
        assert isinstance(method, PinChatMessage)
        assert method.chat_id == message.chat.id
        assert method.message_id == message.message_id

    def test_unpin(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        method = message.unpin()
        assert isinstance(method, UnpinChatMessage)
        assert method.chat_id == message.chat.id

    @pytest.mark.parametrize(
        "text,entities,mode,expected_value",
        [
            ["test", [MessageEntity(type="bold", offset=0, length=4)], "html", "<b>test</b>"],
            ["test", [MessageEntity(type="bold", offset=0, length=4)], "md", "*test*"],
            ["", [], "html", ""],
            ["", [], "md", ""],
        ],
    )
    def test_html_text(self, text, entities, mode, expected_value):
        message = Message(
            message_id=42,
            chat=Chat(id=42, type="private"),
            date=datetime.datetime.now(),
            text=text,
            entities=entities,
        )
        assert getattr(message, f"{mode}_text") == expected_value
