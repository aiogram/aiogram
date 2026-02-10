import datetime
from typing import Any

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
    SendPaidMedia,
    SendPhoto,
    SendPoll,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVideoNote,
    SendVoice,
    SetMessageReaction,
    StopMessageLiveLocation,
    TelegramMethod,
    UnpinChatMessage,
)
from aiogram.types import (
    UNSET_PARSE_MODE,
    Animation,
    Audio,
    BackgroundFillSolid,
    BackgroundTypeFill,
    Chat,
    ChatBackground,
    ChatBoostAdded,
    ChatOwnerChanged,
    ChatOwnerLeft,
    ChatShared,
    Checklist,
    ChecklistTask,
    ChecklistTasksAdded,
    ChecklistTasksDone,
    Contact,
    Dice,
    DirectMessagePriceChanged,
    Document,
    EncryptedCredentials,
    ForumTopicClosed,
    ForumTopicCreated,
    ForumTopicEdited,
    ForumTopicReopened,
    Game,
    GeneralForumTopicHidden,
    GeneralForumTopicUnhidden,
    Gift,
    GiftInfo,
    Giveaway,
    GiveawayCompleted,
    GiveawayCreated,
    GiveawayWinners,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Invoice,
    Location,
    MessageAutoDeleteTimerChanged,
    MessageEntity,
    PaidMediaInfo,
    PaidMediaPhoto,
    PaidMessagePriceChanged,
    PassportData,
    PhotoSize,
    Poll,
    PollOption,
    ProximityAlertTriggered,
    ReactionTypeCustomEmoji,
    RefundedPayment,
    SharedUser,
    Sticker,
    Story,
    SuccessfulPayment,
    SuggestedPostApprovalFailed,
    SuggestedPostApproved,
    SuggestedPostDeclined,
    SuggestedPostPaid,
    SuggestedPostPrice,
    SuggestedPostRefunded,
    UniqueGift,
    UniqueGiftBackdrop,
    UniqueGiftBackdropColors,
    UniqueGiftInfo,
    UniqueGiftModel,
    UniqueGiftSymbol,
    User,
    UserShared,
    UsersShared,
    Venue,
    Video,
    VideoChatEnded,
    VideoChatParticipantsInvited,
    VideoChatScheduled,
    VideoChatStarted,
    VideoNote,
    Voice,
    WebAppData,
    WriteAccessAllowed,
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
TEST_MESSAGE_CHAT_OWNER_LEFT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat_owner_left=ChatOwnerLeft(
        new_owner=User(id=43, is_bot=False, first_name="NewOwner"),
    ),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_CHAT_OWNER_LEFT_NO_SUCCESSOR = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat_owner_left=ChatOwnerLeft(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_CHAT_OWNER_CHANGED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat_owner_changed=ChatOwnerChanged(
        new_owner=User(id=43, is_bot=False, first_name="NewOwner"),
    ),
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
TEST_MESSAGE_PAID_MEDIA = Message(
    message_id=42,
    date=datetime.datetime.now(),
    paid_media=PaidMediaInfo(
        star_count=100500,
        paid_media=[
            PaidMediaPhoto(
                photo=[
                    PhotoSize(file_id="file id", file_unique_id="file id", width=42, height=42)
                ],
            )
        ],
    ),
    chat=Chat(id=42, type="private"),
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
TEST_MESSAGE_USER_SHARED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    user_shared=UserShared(request_id=42, user_id=42),
)
TEST_MESSAGE_USERS_SHARED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=None,
    users_shared=UsersShared(
        request_id=0,
        users=[SharedUser(user_id=1), SharedUser(user_id=2)],
    ),
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
    story=Story(chat=Chat(id=42, type="private"), id=42),
)

TEST_MESSAGE_GIVEAWAY = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=None,
    giveaway=Giveaway(
        chats=[Chat(id=42, type="private")],
        winners_selection_date=datetime.datetime.now() + datetime.timedelta(days=7),
        winner_count=10,
    ),
)
TEST_MESSAGE_GIVEAWAY_CREATED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=None,
    giveaway_created=GiveawayCreated(prize_star_count=42),
)
TEST_MESSAGE_GIVEAWAY_WINNERS = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=None,
    giveaway_winners=GiveawayWinners(
        chat=Chat(id=77, type="private"),
        giveaway_message_id=123,
        winners_selection_date=datetime.datetime.now(),
        winner_count=1,
        winners=[User(id=42, is_bot=False, first_name="Test")],
    ),
)
TEST_MESSAGE_GIVEAWAY_COMPLETED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=None,
    giveaway_completed=GiveawayCompleted(winner_count=10),
)
TEST_MESSAGE_GENERAL_FORUM_TOPIC_HIDDEN = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=None,
    general_forum_topic_hidden=GeneralForumTopicHidden(),
)
TEST_MESSAGE_GENERAL_FORUM_TOPIC_UNHIDDEN = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=None,
    general_forum_topic_unhidden=GeneralForumTopicUnhidden(),
)
TEST_MESSAGE_WRITE_ACCESS_ALLOWED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    write_access_allowed=WriteAccessAllowed(),
)
TEST_MESSAGE_BOOST_ADDED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="User"),
    boost_added=ChatBoostAdded(boost_count=1),
)
TEST_CHAT_BACKGROUND_SET = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="User"),
    chat_background_set=ChatBackground(
        type=BackgroundTypeFill(
            fill=BackgroundFillSolid(color=0x000000),
            dark_theme_dimming=0,
        )
    ),
)
TEST_REFUND_PAYMENT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="User"),
    refunded_payment=RefundedPayment(
        total_amount=42,
        provider_payment_charge_id="payment",
        telegram_payment_charge_id="charge",
        invoice_payload="payload",
    ),
)
TEST_MESSAGE_UNKNOWN = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
TEST_MESSAGE_GIFT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    gift=GiftInfo(
        gift=Gift(
            id="test_gift_id",
            sticker=Sticker(
                file_id="test_file_id",
                file_unique_id="test_file_unique_id",
                type="regular",
                width=512,
                height=512,
                is_animated=False,
                is_video=False,
            ),
            star_count=100,
        ),
        owned_gift_id="test_owned_gift_id",
        convert_star_count=50,
        prepaid_upgrade_star_count=25,
        can_be_upgraded=True,
        text="Test gift message",
        is_private=False,
    ),
)
TEST_MESSAGE_UNIQUE_GIFT = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    unique_gift=UniqueGiftInfo(
        gift=UniqueGift(
            gift_id="test_gift_id",
            base_name="test_gift",
            name="test_unique_gift",
            number=1,
            model=UniqueGiftModel(
                name="test_model",
                sticker=Sticker(
                    file_id="test_file_id",
                    file_unique_id="test_file_unique_id",
                    type="regular",
                    width=512,
                    height=512,
                    is_animated=False,
                    is_video=False,
                ),
                rarity_per_mille=100,
            ),
            symbol=UniqueGiftSymbol(
                name="test_symbol",
                sticker=Sticker(
                    file_id="test_file_id",
                    file_unique_id="test_file_unique_id",
                    type="regular",
                    width=512,
                    height=512,
                    is_animated=False,
                    is_video=False,
                ),
                rarity_per_mille=100,
            ),
            backdrop=UniqueGiftBackdrop(
                name="test_backdrop",
                colors=UniqueGiftBackdropColors(
                    center_color=0xFFFFFF,
                    edge_color=0x000000,
                    symbol_color=0xFF0000,
                    text_color=0x0000FF,
                ),
                rarity_per_mille=100,
            ),
        ),
        origin="upgrade",
    ),
)
TEST_MESSAGE_GIFT_UPGRADE_SENT = Message(
    message_id=42,
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    date=datetime.datetime.now(),
    gift_upgrade_sent=GiftInfo(
        gift=Gift(
            id="test_gift_id",
            sticker=Sticker(
                file_id="test_file_id",
                file_unique_id="test_file_unique_id",
                type="regular",
                width=512,
                height=512,
                is_animated=False,
                is_video=False,
            ),
            star_count=100,
        ),
        owned_gift_id="test_owned_gift_id",
        convert_star_count=50,
        prepaid_upgrade_star_count=25,
        can_be_upgraded=True,
        text="Test gift message",
        is_private=False,
    ),
)
TEST_MESSAGE_CHECKLIST = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    checklist=Checklist(
        title="Test Checklist",
        tasks=[
            ChecklistTask(
                id=1,
                text="Task 1",
            ),
            ChecklistTask(
                id=2,
                text="Task 2",
            ),
        ],
    ),
)
TEST_MESSAGE_CHECKLIST_TASKS_DONE = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    checklist_tasks_done=ChecklistTasksDone(
        marked_as_done_task_ids=[1, 2],
    ),
)
TEST_MESSAGE_CHECKLIST_TASKS_ADDED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    checklist_tasks_added=ChecklistTasksAdded(
        tasks=[
            ChecklistTask(
                id=3,
                text="New Task",
            ),
        ],
    ),
)
TEST_MESSAGE_DIRECT_MESSAGE_PRICE_CHANGED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    direct_message_price_changed=DirectMessagePriceChanged(
        are_direct_messages_enabled=True,
        direct_message_star_count=50,
    ),
)
TEST_MESSAGE_PAID_MESSAGE_PRICE_CHANGED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    paid_message_price_changed=PaidMessagePriceChanged(
        paid_message_star_count=100,
    ),
)
TEST_MESSAGE_SUGGESTED_POST_APPROVED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    suggested_post_approved=SuggestedPostApproved(
        send_date=1234567890,
    ),
)
TEST_MESSAGE_SUGGESTED_POST_APPROVAL_FAILED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    suggested_post_approval_failed=SuggestedPostApprovalFailed(
        price=SuggestedPostPrice(currency="XTR", amount=100),
    ),
)
TEST_MESSAGE_SUGGESTED_POST_DECLINED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    suggested_post_declined=SuggestedPostDeclined(),
)
TEST_MESSAGE_SUGGESTED_POST_PAID = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    suggested_post_paid=SuggestedPostPaid(currency="XTR"),
)
TEST_MESSAGE_SUGGESTED_POST_REFUNDED = Message(
    message_id=42,
    date=datetime.datetime.now(),
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
    suggested_post_refunded=SuggestedPostRefunded(reason="post_deleted"),
)

MESSAGES_AND_CONTENT_TYPES = [
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
    [TEST_MESSAGE_CHECKLIST, ContentType.CHECKLIST],
    [TEST_MESSAGE_CONTACT, ContentType.CONTACT],
    [TEST_MESSAGE_VENUE, ContentType.VENUE],
    [TEST_MESSAGE_LOCATION, ContentType.LOCATION],
    [TEST_MESSAGE_NEW_CHAT_MEMBERS, ContentType.NEW_CHAT_MEMBERS],
    [TEST_MESSAGE_LEFT_CHAT_MEMBER, ContentType.LEFT_CHAT_MEMBER],
    [TEST_MESSAGE_CHAT_OWNER_LEFT, ContentType.CHAT_OWNER_LEFT],
    [TEST_MESSAGE_CHAT_OWNER_CHANGED, ContentType.CHAT_OWNER_CHANGED],
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
    [TEST_MESSAGE_PAID_MEDIA, ContentType.PAID_MEDIA],
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
    [TEST_MESSAGE_USER_SHARED, ContentType.USER_SHARED],
    [TEST_MESSAGE_USERS_SHARED, ContentType.USERS_SHARED],
    [TEST_CHAT_SHARED, ContentType.CHAT_SHARED],
    [TEST_MESSAGE_STORY, ContentType.STORY],
    [TEST_MESSAGE_GIVEAWAY, ContentType.GIVEAWAY],
    [TEST_MESSAGE_GIVEAWAY_CREATED, ContentType.GIVEAWAY_CREATED],
    [TEST_MESSAGE_GIVEAWAY_WINNERS, ContentType.GIVEAWAY_WINNERS],
    [TEST_MESSAGE_GIVEAWAY_COMPLETED, ContentType.GIVEAWAY_COMPLETED],
    [TEST_MESSAGE_GENERAL_FORUM_TOPIC_HIDDEN, ContentType.GENERAL_FORUM_TOPIC_HIDDEN],
    [TEST_MESSAGE_GENERAL_FORUM_TOPIC_UNHIDDEN, ContentType.GENERAL_FORUM_TOPIC_UNHIDDEN],
    [TEST_MESSAGE_WRITE_ACCESS_ALLOWED, ContentType.WRITE_ACCESS_ALLOWED],
    [TEST_MESSAGE_BOOST_ADDED, ContentType.BOOST_ADDED],
    [TEST_CHAT_BACKGROUND_SET, ContentType.CHAT_BACKGROUND_SET],
    [TEST_MESSAGE_CHECKLIST_TASKS_DONE, ContentType.CHECKLIST_TASKS_DONE],
    [TEST_MESSAGE_CHECKLIST_TASKS_ADDED, ContentType.CHECKLIST_TASKS_ADDED],
    [TEST_MESSAGE_DIRECT_MESSAGE_PRICE_CHANGED, ContentType.DIRECT_MESSAGE_PRICE_CHANGED],
    [TEST_REFUND_PAYMENT, ContentType.REFUNDED_PAYMENT],
    [TEST_MESSAGE_GIFT, ContentType.GIFT],
    [TEST_MESSAGE_UNIQUE_GIFT, ContentType.UNIQUE_GIFT],
    [TEST_MESSAGE_GIFT_UPGRADE_SENT, ContentType.GIFT_UPGRADE_SENT],
    [TEST_MESSAGE_PAID_MESSAGE_PRICE_CHANGED, ContentType.PAID_MESSAGE_PRICE_CHANGED],
    [TEST_MESSAGE_SUGGESTED_POST_APPROVED, ContentType.SUGGESTED_POST_APPROVED],
    [TEST_MESSAGE_SUGGESTED_POST_APPROVAL_FAILED, ContentType.SUGGESTED_POST_APPROVAL_FAILED],
    [TEST_MESSAGE_SUGGESTED_POST_DECLINED, ContentType.SUGGESTED_POST_DECLINED],
    [TEST_MESSAGE_SUGGESTED_POST_PAID, ContentType.SUGGESTED_POST_PAID],
    [TEST_MESSAGE_SUGGESTED_POST_REFUNDED, ContentType.SUGGESTED_POST_REFUNDED],
    [TEST_MESSAGE_UNKNOWN, ContentType.UNKNOWN],
]


MESSAGES_AND_COPY_METHODS = [
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
    [TEST_MESSAGE_CHECKLIST, None],
    [TEST_MESSAGE_CONTACT, SendContact],
    [TEST_MESSAGE_VENUE, SendVenue],
    [TEST_MESSAGE_LOCATION, SendLocation],
    [TEST_MESSAGE_STORY, ForwardMessage],
    [TEST_MESSAGE_NEW_CHAT_MEMBERS, None],
    [TEST_MESSAGE_LEFT_CHAT_MEMBER, None],
    [TEST_MESSAGE_CHAT_OWNER_LEFT, None],
    [TEST_MESSAGE_CHAT_OWNER_CHANGED, None],
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
    [TEST_MESSAGE_PAID_MEDIA, None],
    [TEST_MESSAGE_PASSPORT_DATA, None],
    [TEST_MESSAGE_PROXIMITY_ALERT_TRIGGERED, None],
    [TEST_MESSAGE_POLL, SendPoll],
    [TEST_MESSAGE_MESSAGE_AUTO_DELETE_TIMER_CHANGED, None],
    [TEST_MESSAGE_VIDEO_CHAT_STARTED, None],
    [TEST_MESSAGE_VIDEO_CHAT_ENDED, None],
    [TEST_MESSAGE_VIDEO_CHAT_PARTICIPANTS_INVITED, None],
    [TEST_MESSAGE_DICE, SendDice],
    [TEST_MESSAGE_USER_SHARED, None],
    [TEST_CHAT_SHARED, None],
    [TEST_MESSAGE_GIVEAWAY_COMPLETED, None],
    [TEST_MESSAGE_WEB_APP_DATA, None],
    [TEST_FORUM_TOPIC_CREATED, None],
    [TEST_FORUM_TOPIC_EDITED, None],
    [TEST_FORUM_TOPIC_CLOSED, None],
    [TEST_FORUM_TOPIC_REOPENED, None],
    [TEST_MESSAGE_GENERAL_FORUM_TOPIC_HIDDEN, None],
    [TEST_MESSAGE_GENERAL_FORUM_TOPIC_UNHIDDEN, None],
    [TEST_MESSAGE_GIVEAWAY_CREATED, None],
    [TEST_MESSAGE_USERS_SHARED, None],
    [TEST_MESSAGE_VIDEO_CHAT_SCHEDULED, None],
    [TEST_MESSAGE_WRITE_ACCESS_ALLOWED, None],
    [TEST_MESSAGE_GIVEAWAY, None],
    [TEST_MESSAGE_GIVEAWAY_WINNERS, None],
    [TEST_MESSAGE_BOOST_ADDED, None],
    [TEST_CHAT_BACKGROUND_SET, None],
    [TEST_MESSAGE_CHECKLIST_TASKS_DONE, None],
    [TEST_MESSAGE_CHECKLIST_TASKS_ADDED, None],
    [TEST_MESSAGE_DIRECT_MESSAGE_PRICE_CHANGED, None],
    [TEST_REFUND_PAYMENT, None],
    [TEST_MESSAGE_GIFT, None],
    [TEST_MESSAGE_UNIQUE_GIFT, None],
    [TEST_MESSAGE_GIFT_UPGRADE_SENT, None],
    [TEST_MESSAGE_PAID_MESSAGE_PRICE_CHANGED, None],
    [TEST_MESSAGE_SUGGESTED_POST_APPROVED, None],
    [TEST_MESSAGE_SUGGESTED_POST_APPROVAL_FAILED, None],
    [TEST_MESSAGE_SUGGESTED_POST_DECLINED, None],
    [TEST_MESSAGE_SUGGESTED_POST_PAID, None],
    [TEST_MESSAGE_SUGGESTED_POST_REFUNDED, None],
    [TEST_MESSAGE_UNKNOWN, None],
]


class TestAllMessageTypesTested:
    @pytest.fixture(scope="function")
    def known_content_types(self):
        content_types = set(ContentType)
        content_types.remove(ContentType.ANY)
        return content_types

    def test_for_content_type_tests(self, known_content_types):
        """
        Test if all ContentType options have example messages.

        On new Bot API updates new ContentType entries are created.
        TestMessage.test_content_type checks what content type is returned.
        Make sure MESSAGES_AND_CONTENT_TYPES has examples
        for all the ContentType entries, fail otherwise.
        """
        content_types_w_example_messages = {t[1] for t in MESSAGES_AND_CONTENT_TYPES}
        assert content_types_w_example_messages == known_content_types

    def test_for_copy_methods(self, known_content_types):
        """
        Test if all known message types are checked for copy_message.

        Also relies on the previous test (both should be green)
        """
        checked_content_types = {m[0].content_type for m in MESSAGES_AND_COPY_METHODS}
        assert checked_content_types == known_content_types


class TestMessage:
    @pytest.mark.parametrize(
        "message,content_type",
        MESSAGES_AND_CONTENT_TYPES,
    )
    def test_content_type(self, message: Message, content_type: str):
        assert message.content_type == content_type

    def test_chat_owner_left_no_successor(self):
        assert (
            TEST_MESSAGE_CHAT_OWNER_LEFT_NO_SUCCESSOR.content_type == ContentType.CHAT_OWNER_LEFT
        )

    def test_as_reply_parameters(self):
        message = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
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
            assert api_method.reply_parameters
            assert api_method.reply_parameters.message_id == message.message_id
            assert api_method.reply_parameters.chat_id == message.chat.id
        else:
            assert api_method.reply_parameters is None

        if hasattr(api_method, "reply_to_message_id"):
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
        MESSAGES_AND_COPY_METHODS,
    )
    def test_send_copy(
        self,
        message: Message,
        expected_method: type[TelegramMethod] | None,
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
        expected_method: type[TelegramMethod] | None,
        custom_parse_mode: str | None,
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

    def test_react(self):
        message = Message(
            message_id=777,
            chat=Chat(id=-42, type="channel"),
            date=datetime.datetime.now(),
        )
        emoji_reaction = ReactionTypeCustomEmoji(custom_emoji_id="qwerty")
        method = message.react(
            reaction=[emoji_reaction],
        )
        assert isinstance(method, SetMessageReaction)
        assert method.chat_id == message.chat.id
        assert method.reaction == [emoji_reaction]

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
