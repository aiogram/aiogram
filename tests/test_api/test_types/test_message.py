import datetime

import pytest

from aiogram.api.types import (
    Animation,
    Audio,
    Chat,
    Contact,
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
)
from aiogram.api.types.message import ContentType, Message


class TestMessage:
    @pytest.mark.parametrize(
        "message,content_type",
        [
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="test",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.TEXT,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    audio=Audio(file_id="file id", file_unique_id="file id", duration=42),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.ANIMATION,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    document=Document(file_id="file id", file_unique_id="file id"),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.VIDEO_NOTE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    voice=Voice(file_id="file id", file_unique_id="file id", duration=0),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.VOICE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    contact=Contact(phone_number="911", first_name="911"),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.VENUE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    location=Location(longitude=3.14, latitude=3.14),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.LOCATION,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    new_chat_members=[User(id=42, is_bot=False, first_name="Test")],
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.NEW_CHAT_MEMBERS,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    left_chat_member=User(id=42, is_bot=False, first_name="Test"),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.SUCCESSFUL_PAYMENT,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    connected_website="token",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.CONNECTED_WEBSITE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    migrate_from_chat_id=42,
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.MIGRATE_FROM_CHAT_ID,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    migrate_to_chat_id=42,
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                        chat=Chat(id=42, type="private"),
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                    ),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.PINNED_MESSAGE,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    new_chat_title="test",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.NEW_CHAT_PHOTO,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    delete_chat_photo=True,
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.DELETE_CHAT_PHOTO,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    group_chat_created=True,
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
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
                    ),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.POLL,
            ],
            [
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
                ContentType.UNKNOWN,
            ],
        ],
    )
    def test_content_type(self, message: Message, content_type: str):
        assert message.content_type == content_type
