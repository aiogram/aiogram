import pytest

from aiogram import Bot, types
from . import FakeTelegram, TOKEN, BOT_ID

pytestmark = pytest.mark.asyncio


@pytest.yield_fixture(name='bot')
async def bot_fixture(event_loop):
    """ Bot fixture """
    _bot = Bot(TOKEN, loop=event_loop, parse_mode=types.ParseMode.MARKDOWN)
    yield _bot
    await _bot.close()


async def test_get_me(bot: Bot, event_loop):
    """ getMe method test """
    from .types.dataset import USER
    user = types.User(**USER)

    async with FakeTelegram(message_data=USER, loop=event_loop):
        result = await bot.me
        assert result == user


async def test_send_message(bot: Bot, event_loop):
    """ sendMessage method test """
    from .types.dataset import MESSAGE
    msg = types.Message(**MESSAGE)

    async with FakeTelegram(message_data=MESSAGE, loop=event_loop):
        result = await bot.send_message(chat_id=msg.chat.id, text=msg.text)
        assert result == msg


async def test_forward_message(bot: Bot, event_loop):
    """ forwardMessage method test """
    from .types.dataset import FORWARDED_MESSAGE
    msg = types.Message(**FORWARDED_MESSAGE)

    async with FakeTelegram(message_data=FORWARDED_MESSAGE, loop=event_loop):
        result = await bot.forward_message(chat_id=msg.chat.id, from_chat_id=msg.forward_from_chat.id,
                                           message_id=msg.forward_from_message_id)
        assert result == msg


async def test_send_photo(bot: Bot, event_loop):
    """ sendPhoto method test with file_id """
    from .types.dataset import MESSAGE_WITH_PHOTO, PHOTO
    msg = types.Message(**MESSAGE_WITH_PHOTO)
    photo = types.PhotoSize(**PHOTO)

    async with FakeTelegram(message_data=MESSAGE_WITH_PHOTO, loop=event_loop):
        result = await bot.send_photo(msg.chat.id, photo=photo.file_id, caption=msg.caption,
                                      parse_mode=types.ParseMode.HTML, disable_notification=False)
        assert result == msg


async def test_send_audio(bot: Bot, event_loop):
    """ sendAudio method test with file_id """
    from .types.dataset import MESSAGE_WITH_AUDIO
    msg = types.Message(**MESSAGE_WITH_AUDIO)

    async with FakeTelegram(message_data=MESSAGE_WITH_AUDIO, loop=event_loop):
        result = await bot.send_audio(chat_id=msg.chat.id, audio=msg.audio.file_id, caption=msg.caption,
                                      parse_mode=types.ParseMode.HTML, duration=msg.audio.duration,
                                      performer=msg.audio.performer, title=msg.audio.title, disable_notification=False)
        assert result == msg


async def test_send_document(bot: Bot, event_loop):
    """ sendDocument method test with file_id """
    from .types.dataset import MESSAGE_WITH_DOCUMENT
    msg = types.Message(**MESSAGE_WITH_DOCUMENT)

    async with FakeTelegram(message_data=MESSAGE_WITH_DOCUMENT, loop=event_loop):
        result = await bot.send_document(chat_id=msg.chat.id, document=msg.document.file_id, caption=msg.caption,
                                         parse_mode=types.ParseMode.HTML, disable_notification=False)
        assert result == msg


async def test_send_video(bot: Bot, event_loop):
    """ sendVideo method test with file_id """
    from .types.dataset import MESSAGE_WITH_VIDEO, VIDEO
    msg = types.Message(**MESSAGE_WITH_VIDEO)
    video = types.Video(**VIDEO)

    async with FakeTelegram(message_data=MESSAGE_WITH_VIDEO, loop=event_loop):
        result = await bot.send_video(chat_id=msg.chat.id, video=video.file_id, duration=video.duration,
                                      width=video.width, height=video.height, caption=msg.caption,
                                      parse_mode=types.ParseMode.HTML, supports_streaming=True,
                                      disable_notification=False)
        assert result == msg


async def test_send_voice(bot: Bot, event_loop):
    """ sendVoice method test with file_id """
    from .types.dataset import MESSAGE_WITH_VOICE, VOICE
    msg = types.Message(**MESSAGE_WITH_VOICE)
    voice = types.Voice(**VOICE)

    async with FakeTelegram(message_data=MESSAGE_WITH_VOICE, loop=event_loop):
        result = await bot.send_voice(chat_id=msg.chat.id, voice=voice.file_id, caption=msg.caption,
                                      parse_mode=types.ParseMode.HTML, duration=voice.duration,
                                      disable_notification=False)
        assert result == msg


async def test_send_video_note(bot: Bot, event_loop):
    """ sendVideoNote method test with file_id """
    from .types.dataset import MESSAGE_WITH_VIDEO_NOTE, VIDEO_NOTE
    msg = types.Message(**MESSAGE_WITH_VIDEO_NOTE)
    video_note = types.VideoNote(**VIDEO_NOTE)

    async with FakeTelegram(message_data=MESSAGE_WITH_VIDEO_NOTE, loop=event_loop):
        result = await bot.send_video_note(chat_id=msg.chat.id, video_note=video_note.file_id,
                                           duration=video_note.duration, length=video_note.length,
                                           disable_notification=False)
        assert result == msg


async def test_send_media_group(bot: Bot, event_loop):
    """ sendMediaGroup method test with file_id """
    from .types.dataset import MESSAGE_WITH_MEDIA_GROUP, PHOTO
    msg = types.Message(**MESSAGE_WITH_MEDIA_GROUP)
    photo = types.PhotoSize(**PHOTO)
    media = [types.InputMediaPhoto(media=photo.file_id), types.InputMediaPhoto(media=photo.file_id)]

    async with FakeTelegram(message_data=[MESSAGE_WITH_MEDIA_GROUP, MESSAGE_WITH_MEDIA_GROUP], loop=event_loop):
        result = await bot.send_media_group(msg.chat.id, media=media, disable_notification=False)
        assert len(result) == len(media)
        assert result.pop().media_group_id


async def test_send_location(bot: Bot, event_loop):
    """ sendLocation method test """
    from .types.dataset import MESSAGE_WITH_LOCATION, LOCATION
    msg = types.Message(**MESSAGE_WITH_LOCATION)
    location = types.Location(**LOCATION)

    async with FakeTelegram(message_data=MESSAGE_WITH_LOCATION, loop=event_loop):
        result = await bot.send_location(msg.chat.id, latitude=location.latitude, longitude=location.longitude,
                                         live_period=10, disable_notification=False)
        assert result == msg


async def test_edit_message_live_location_by_bot(bot: Bot, event_loop):
    """ editMessageLiveLocation method test """
    from .types.dataset import MESSAGE_WITH_LOCATION, LOCATION
    msg = types.Message(**MESSAGE_WITH_LOCATION)
    location = types.Location(**LOCATION)

    # editing bot message
    async with FakeTelegram(message_data=MESSAGE_WITH_LOCATION, loop=event_loop):
        result = await bot.edit_message_live_location(chat_id=msg.chat.id, message_id=msg.message_id,
                                                      latitude=location.latitude, longitude=location.longitude)
        assert result == msg


async def test_edit_message_live_location_by_user(bot: Bot, event_loop):
    """ editMessageLiveLocation method test """
    from .types.dataset import MESSAGE_WITH_LOCATION, LOCATION
    msg = types.Message(**MESSAGE_WITH_LOCATION)
    location = types.Location(**LOCATION)

    # editing user's message
    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.edit_message_live_location(chat_id=msg.chat.id, message_id=msg.message_id,
                                                      latitude=location.latitude, longitude=location.longitude)
        assert isinstance(result, bool) and result is True


async def test_stop_message_live_location_by_bot(bot: Bot, event_loop):
    """ stopMessageLiveLocation method test """
    from .types.dataset import MESSAGE_WITH_LOCATION
    msg = types.Message(**MESSAGE_WITH_LOCATION)

    # stopping bot message
    async with FakeTelegram(message_data=MESSAGE_WITH_LOCATION, loop=event_loop):
        result = await bot.stop_message_live_location(chat_id=msg.chat.id, message_id=msg.message_id)
        assert result == msg


async def test_stop_message_live_location_by_user(bot: Bot, event_loop):
    """ stopMessageLiveLocation method test """
    from .types.dataset import MESSAGE_WITH_LOCATION
    msg = types.Message(**MESSAGE_WITH_LOCATION)

    # stopping user's message
    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.stop_message_live_location(chat_id=msg.chat.id, message_id=msg.message_id)
        assert isinstance(result, bool)
        assert result is True


async def test_send_venue(bot: Bot, event_loop):
    """ sendVenue method test """
    from .types.dataset import MESSAGE_WITH_VENUE, VENUE, LOCATION
    msg = types.Message(**MESSAGE_WITH_VENUE)
    location = types.Location(**LOCATION)
    venue = types.Venue(**VENUE)

    async with FakeTelegram(message_data=MESSAGE_WITH_VENUE, loop=event_loop):
        result = await bot.send_venue(msg.chat.id, latitude=location.latitude, longitude=location.longitude,
                                      title=venue.title, address=venue.address, foursquare_id=venue.foursquare_id,
                                      disable_notification=False)
        assert result == msg


async def test_send_contact(bot: Bot, event_loop):
    """ sendContact method test """
    from .types.dataset import MESSAGE_WITH_CONTACT, CONTACT
    msg = types.Message(**MESSAGE_WITH_CONTACT)
    contact = types.Contact(**CONTACT)

    async with FakeTelegram(message_data=MESSAGE_WITH_CONTACT, loop=event_loop):
        result = await bot.send_contact(msg.chat.id, phone_number=contact.phone_number, first_name=contact.first_name,
                                        last_name=contact.last_name, disable_notification=False)
        assert result == msg


async def test_send_dice(bot: Bot, event_loop):
    """ sendDice method test """
    from .types.dataset import MESSAGE_WITH_DICE
    msg = types.Message(**MESSAGE_WITH_DICE)

    async with FakeTelegram(message_data=MESSAGE_WITH_DICE, loop=event_loop):
        result = await bot.send_dice(msg.chat.id, disable_notification=False)
        assert result == msg


async def test_send_chat_action(bot: Bot, event_loop):
    """ sendChatAction method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.send_chat_action(chat_id=chat.id, action=types.ChatActions.TYPING)
        assert isinstance(result, bool)
        assert result is True


async def test_get_user_profile_photo(bot: Bot, event_loop):
    """ getUserProfilePhotos method test """
    from .types.dataset import USER_PROFILE_PHOTOS, USER
    user = types.User(**USER)

    async with FakeTelegram(message_data=USER_PROFILE_PHOTOS, loop=event_loop):
        result = await bot.get_user_profile_photos(user_id=user.id, offset=1, limit=1)
        assert isinstance(result, types.UserProfilePhotos)


async def test_get_file(bot: Bot, event_loop):
    """ getFile method test """
    from .types.dataset import FILE
    file = types.File(**FILE)

    async with FakeTelegram(message_data=FILE, loop=event_loop):
        result = await bot.get_file(file_id=file.file_id)
        assert isinstance(result, types.File)


async def test_kick_chat_member(bot: Bot, event_loop):
    """ kickChatMember method test """
    from .types.dataset import USER, CHAT
    user = types.User(**USER)
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.kick_chat_member(chat_id=chat.id, user_id=user.id, until_date=123)
        assert isinstance(result, bool)
        assert result is True


async def test_unban_chat_member(bot: Bot, event_loop):
    """ unbanChatMember method test """
    from .types.dataset import USER, CHAT
    user = types.User(**USER)
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.unban_chat_member(chat_id=chat.id, user_id=user.id)
        assert isinstance(result, bool)
        assert result is True


async def test_restrict_chat_member(bot: Bot, event_loop):
    """ restrictChatMember method test """
    from .types.dataset import USER, CHAT
    user = types.User(**USER)
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            permissions=types.ChatPermissions(
                can_add_web_page_previews=False,
                can_send_media_messages=False,
                can_send_messages=False,
                can_send_other_messages=False
            ), until_date=123)
        assert isinstance(result, bool)
        assert result is True


async def test_promote_chat_member(bot: Bot, event_loop):
    """ promoteChatMember method test """
    from .types.dataset import USER, CHAT
    user = types.User(**USER)
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.promote_chat_member(chat_id=chat.id, user_id=user.id, can_change_info=True,
                                               can_delete_messages=True, can_edit_messages=True,
                                               can_invite_users=True, can_pin_messages=True, can_post_messages=True,
                                               can_promote_members=True, can_restrict_members=True)
        assert isinstance(result, bool)
        assert result is True


async def test_export_chat_invite_link(bot: Bot, event_loop):
    """ exportChatInviteLink method test """
    from .types.dataset import CHAT, INVITE_LINK
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=INVITE_LINK, loop=event_loop):
        result = await bot.export_chat_invite_link(chat_id=chat.id)
        assert result == INVITE_LINK


async def test_delete_chat_photo(bot: Bot, event_loop):
    """ deleteChatPhoto method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.delete_chat_photo(chat_id=chat.id)
        assert isinstance(result, bool)
        assert result is True


async def test_set_chat_title(bot: Bot, event_loop):
    """ setChatTitle method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.set_chat_title(chat_id=chat.id, title='Test title')
        assert isinstance(result, bool)
        assert result is True


async def test_set_chat_description(bot: Bot, event_loop):
    """ setChatDescription method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.set_chat_description(chat_id=chat.id, description='Test description')
        assert isinstance(result, bool)
        assert result is True


async def test_pin_chat_message(bot: Bot, event_loop):
    """ pinChatMessage method test """
    from .types.dataset import MESSAGE
    message = types.Message(**MESSAGE)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.pin_chat_message(chat_id=message.chat.id, message_id=message.message_id,
                                            disable_notification=False)
        assert isinstance(result, bool)
        assert result is True


async def test_unpin_chat_message(bot: Bot, event_loop):
    """ unpinChatMessage method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.unpin_chat_message(chat_id=chat.id)
        assert isinstance(result, bool)
        assert result is True


async def test_leave_chat(bot: Bot, event_loop):
    """ leaveChat method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.leave_chat(chat_id=chat.id)
        assert isinstance(result, bool)
        assert result is True


async def test_get_chat(bot: Bot, event_loop):
    """ getChat method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=CHAT, loop=event_loop):
        result = await bot.get_chat(chat_id=chat.id)
        assert result == chat


async def test_get_chat_administrators(bot: Bot, event_loop):
    """ getChatAdministrators method test """
    from .types.dataset import CHAT, CHAT_MEMBER
    chat = types.Chat(**CHAT)
    member = types.ChatMember(**CHAT_MEMBER)

    async with FakeTelegram(message_data=[CHAT_MEMBER, CHAT_MEMBER], loop=event_loop):
        result = await bot.get_chat_administrators(chat_id=chat.id)
        assert result[0] == member
        assert len(result) == 2


async def test_get_chat_members_count(bot: Bot, event_loop):
    """ getChatMembersCount method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)
    count = 5

    async with FakeTelegram(message_data=count, loop=event_loop):
        result = await bot.get_chat_members_count(chat_id=chat.id)
        assert result == count


async def test_get_chat_member(bot: Bot, event_loop):
    """ getChatMember method test """
    from .types.dataset import CHAT, CHAT_MEMBER
    chat = types.Chat(**CHAT)
    member = types.ChatMember(**CHAT_MEMBER)

    async with FakeTelegram(message_data=CHAT_MEMBER, loop=event_loop):
        result = await bot.get_chat_member(chat_id=chat.id, user_id=member.user.id)
        assert isinstance(result, types.ChatMember)
        assert result == member


async def test_set_chat_sticker_set(bot: Bot, event_loop):
    """ setChatStickerSet method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.set_chat_sticker_set(chat_id=chat.id, sticker_set_name='aiogram_stickers')
        assert isinstance(result, bool)
        assert result is True


async def test_delete_chat_sticker_set(bot: Bot, event_loop):
    """ setChatStickerSet method test """
    from .types.dataset import CHAT
    chat = types.Chat(**CHAT)

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.delete_chat_sticker_set(chat_id=chat.id)
        assert isinstance(result, bool)
        assert result is True


async def test_answer_callback_query(bot: Bot, event_loop):
    """ answerCallbackQuery method test """

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.answer_callback_query(callback_query_id='QuERyId', text='Test Answer')
        assert isinstance(result, bool)
        assert result is True


async def test_set_my_commands(bot: Bot, event_loop):
    """ setMyCommands method test """
    from .types.dataset import BOT_COMMAND

    async with FakeTelegram(message_data=True, loop=event_loop):
        commands = [types.BotCommand(**BOT_COMMAND), types.BotCommand(**BOT_COMMAND)]
        result = await bot.set_my_commands(commands)
        assert isinstance(result, bool)
        assert result is True


async def test_get_my_commands(bot: Bot, event_loop):
    """ getMyCommands method test """
    from .types.dataset import BOT_COMMAND
    command = types.BotCommand(**BOT_COMMAND)
    commands = [command, command]
    async with FakeTelegram(message_data=commands, loop=event_loop):
        result = await bot.get_my_commands()
        assert isinstance(result, list)
        assert all([isinstance(command, types.BotCommand) for command in result])


async def test_edit_message_text_by_bot(bot: Bot, event_loop):
    """ editMessageText method test """
    from .types.dataset import EDITED_MESSAGE
    msg = types.Message(**EDITED_MESSAGE)

    # message by bot
    async with FakeTelegram(message_data=EDITED_MESSAGE, loop=event_loop):
        result = await bot.edit_message_text(text=msg.text, chat_id=msg.chat.id, message_id=msg.message_id)
        assert result == msg


async def test_edit_message_text_by_user(bot: Bot, event_loop):
    """ editMessageText method test """
    from .types.dataset import EDITED_MESSAGE
    msg = types.Message(**EDITED_MESSAGE)

    # message by user
    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.edit_message_text(text=msg.text, chat_id=msg.chat.id, message_id=msg.message_id)
        assert isinstance(result, bool)
        assert result is True


async def test_set_sticker_set_thumb(bot: Bot, event_loop):
    """ setStickerSetThumb method test """

    async with FakeTelegram(message_data=True, loop=event_loop):
        result = await bot.set_sticker_set_thumb(name='test', user_id=123456789, thumb='file_id')
        assert isinstance(result, bool)
        assert result is True


async def test_bot_id(bot: Bot):
    """ Check getting id from token. """
    bot = Bot(TOKEN)
    assert bot.id == BOT_ID  # BOT_ID is a correct id from TOKEN
