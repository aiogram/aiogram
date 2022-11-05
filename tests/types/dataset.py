""""
Dict data set for Telegram message types
"""

USER = {
    "id": 12345678,
    "is_bot": False,
    "first_name": "FirstName",
    "last_name": "LastName",
    "username": "username",
    "language_code": "ru",
}

CHAT = {
    "id": 12345678,
    "first_name": "FirstName",
    "last_name": "LastName",
    "username": "username",
    "type": "private",
}

CHAT_PHOTO = {
    "small_file_id": "small_file_id",
    "small_file_unique_id": "small_file_unique_id",
    "big_file_id": "big_file_id",
    "big_file_unique_id": "big_file_unique_id",
}


PHOTO = {
    "file_id": "AgADBAADFak0G88YZAf8OAug7bHyS9x2ZxkABHVfpJywcloRAAGAAQABAg",
    "file_size": 1101,
    "width": 90,
    "height": 51,
}

AUDIO = {
    "duration": 236,
    "mime_type": "audio/mpeg3",
    "title": "The Best Song",
    "performer": "The Best Singer",
    "file_id": "CQADAgADbQEAAsnrIUpNoRRNsH7_hAI",
    "file_size": 9507774,
}

BOT_COMMAND = {
    "command": "start",
    "description": "Start bot",
}

CHAT_MEMBER = {
    "user": USER,
    "status": "administrator",
    "can_be_edited": False,
    "can_manage_chat": True,
    "can_change_info": True,
    "can_delete_messages": True,
    "can_invite_users": True,
    "can_restrict_members": True,
    "can_pin_messages": True,
    "can_promote_members": False,
    "can_manage_voice_chats": True,  # Deprecated
    "can_manage_video_chats": True,
    "can_manage_topics": True,
    "is_anonymous": False,
}

CHAT_MEMBER_OWNER = {
    "user": USER,
    "status": "creator",
    "is_anonymous": False,
}

CONTACT = {
    "phone_number": "88005553535",
    "first_name": "John",
    "last_name": "Smith",
}

DICE = {
    "value": 6
}

DOCUMENT = {
    "file_name": "test.docx",
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_id": "BQADAgADpgADy_JxS66XQTBRHFleAg",
    "file_size": 21331,
}

ANIMATION = {
    "file_name": "a9b0e0ca537aa344338f80978f0896b7.gif.mp4",
    "mime_type": "video/mp4",
    "thumb": PHOTO,
    "file_id": "CgADBAAD4DUAAoceZAe2WiE9y0crrAI",
    "file_size": 65837,
}

ENTITY_BOLD = {
    "offset": 5,
    "length": 2,
    "type": "bold",
}

ENTITY_ITALIC = {
    "offset": 8,
    "length": 1,
    "type": "italic",
}

ENTITY_LINK = {
    "offset": 10,
    "length": 6,
    "type": "text_link",
    "url": "https://google.com/",
}

ENTITY_CODE = {
    "offset": 17,
    "length": 7,
    "type": "code",
}

ENTITY_PRE = {
    "offset": 30,
    "length": 4,
    "type": "pre",
}

ENTITY_MENTION = {
    "offset": 47,
    "length": 9,
    "type": "mention",
}

GAME = {
    "title": "Karate Kido",
    "description": "No trees were harmed in the making of this game :)",
    "photo": [PHOTO, PHOTO, PHOTO],
    "animation": ANIMATION,
}

INVOICE = {
    "title": "Working Time Machine",
    "description": "Want to visit your great-great-great-grandparents? "
                   "Make a fortune at the races? "
                   "Shake hands with Hammurabi and take a stroll in the Hanging Gardens? "
                   "Order our Working Time Machine today!",
    "start_parameter": "time-machine-example",
    "currency": "USD",
    "total_amount": 6250,
}

LOCATION = {
    "latitude": 50.693416,
    "longitude": 30.624605,
}

VENUE = {
    "location": LOCATION,
    "title": "Venue Name",
    "address": "Venue Address",
    "foursquare_id": "4e6f2cec483bad563d150f98",
}

SHIPPING_ADDRESS = {
    "country_code": "US",
    "state": "State",
    "city": "DefaultCity",
    "street_line1": "Central",
    "street_line2": "Middle",
    "post_code": "424242",
}

STICKER = {
    "width": 512,
    "height": 512,
    "emoji": "🛠",
    "set_name": "StickerSet",
    "thumb": {
        "file_id": "AAbbCCddEEffGGhh1234567890",
        "file_size": 1234,
        "width": 128,
        "height": 128
    },
    "file_id": "AAbbCCddEEffGGhh1234567890",
    "file_size": 12345,
}

SUCCESSFUL_PAYMENT = {
    "currency": "USD",
    "total_amount": 6250,
    "invoice_payload": "HAPPY FRIDAYS COUPON",
    "telegram_payment_charge_id": "_",
    "provider_payment_charge_id": "12345678901234_test",
}

VIDEO = {
    "duration": 52,
    "width": 853,
    "height": 480,
    "mime_type": "video/quicktime",
    "thumb": PHOTO,
    "file_id": "BAADAgpAADdawy_JxS72kRvV3cortAg",
    "file_size": 10099782,
}

VIDEO_NOTE = {
    "duration": 4,
    "length": 240,
    "thumb": PHOTO,
    "file_id": "AbCdEfGhIjKlMnOpQrStUvWxYz",
    "file_size": 186562,
}

VOICE = {
    "duration": 1,
    "mime_type": "audio/ogg",
    "file_id": "AwADawAgADADy_JxS2gopIVIIxlhAg",
    "file_size": 4321,
}

CALLBACK_QUERY = {}

CHANNEL_POST = {}

CHOSEN_INLINE_RESULT = {}

EDITED_CHANNEL_POST = {}

EDITED_MESSAGE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508825372,
    "edit_date": 1508825379,
    "text": "hi there (edited)",
}

FORWARDED_MESSAGE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1522828529,
    "forward_from_chat": CHAT,
    "forward_from_message_id": 123,
    "forward_date": 1522749037,
    "text": "Forwarded text with entities from public channel ",
    "entities": [ENTITY_BOLD, ENTITY_CODE, ENTITY_ITALIC, ENTITY_LINK,
                 ENTITY_LINK, ENTITY_MENTION, ENTITY_PRE],
}

INLINE_QUERY = {}

MESSAGE = {
    "message_id": 11223,
    "from": USER,
    "chat": CHAT,
    "date": 1508709711,
    "text": "Hi, world!",
}

MESSAGE_WITH_AUDIO = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508739776,
    "audio": AUDIO,
    "caption": "This is my favourite song",
}

MESSAGE_WITH_AUTHOR_SIGNATURE = {}

MESSAGE_WITH_CHANNEL_CHAT_CREATED = {}

MESSAGE_WITH_CONTACT = {
    "message_id": 56006,
    "from": USER,
    "chat": CHAT,
    "date": 1522850298,
    "contact": CONTACT,
}

MESSAGE_WITH_DELETE_CHAT_PHOTO = {}

MESSAGE_WITH_DICE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508768012,
    "dice": DICE
}

MESSAGE_WITH_DOCUMENT = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508768012,
    "document": DOCUMENT,
    "caption": "Read my document",
}

MESSAGE_WITH_EDIT_DATE = {}

MESSAGE_WITH_ENTITIES = {}

MESSAGE_WITH_GAME = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508824810,
    "game": GAME,
}

MESSAGE_WITH_GROUP_CHAT_CREATED = {}

MESSAGE_WITH_INVOICE = {
    "message_id": 9772,
    "from": USER,
    "chat": CHAT,
    "date": 1508761719,
    "invoice": INVOICE,
}

MESSAGE_WITH_LEFT_CHAT_MEMBER = {}

MESSAGE_WITH_LOCATION = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508755473,
    "location": LOCATION,
}

MESSAGE_WITH_MIGRATE_TO_CHAT_ID = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1526943253,
    "migrate_to_chat_id": -1234567890987,
}

MESSAGE_WITH_MIGRATE_FROM_CHAT_ID = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1526943253,
    "migrate_from_chat_id": -123456789,
}

MESSAGE_WITH_NEW_CHAT_MEMBERS = {}

MESSAGE_WITH_NEW_CHAT_PHOTO = {}

MESSAGE_WITH_NEW_CHAT_TITLE = {}

MESSAGE_WITH_PHOTO = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508825154,
    "photo": [PHOTO, PHOTO, PHOTO, PHOTO],
    "caption": "photo description",
}

MESSAGE_WITH_MEDIA_GROUP = {
    "message_id": 55966,
    "from": USER,
    "chat": CHAT,
    "date": 1522843665,
    "media_group_id": "12182749320567362",
    "photo": [PHOTO, PHOTO, PHOTO, PHOTO],
}

MESSAGE_WITH_PINNED_MESSAGE = {}

MESSAGE_WITH_REPLY_TO_MESSAGE = {}

MESSAGE_WITH_STICKER = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508771450,
    "sticker": STICKER,
}

MESSAGE_WITH_SUCCESSFUL_PAYMENT = {
    "message_id": 9768,
    "from": USER,
    "chat": CHAT,
    "date": 1508761169,
    "successful_payment": SUCCESSFUL_PAYMENT,
}

MESSAGE_WITH_SUPERGROUP_CHAT_CREATED = {}

MESSAGE_WITH_VENUE = {
    "message_id": 56004,
    "from": USER,
    "chat": CHAT,
    "date": 1522849819,
    "location": LOCATION,
    "venue": VENUE,
}

MESSAGE_WITH_VIDEO = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508756494,
    "video": VIDEO,
    "caption": "description",
}

MESSAGE_WITH_VIDEO_NOTE = {
    "message_id": 55934,
    "from": USER,
    "chat": CHAT,
    "date": 1522835890,
    "video_note": VIDEO_NOTE,
}

MESSAGE_WITH_VOICE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508768403,
    "voice": VOICE,
}

CHANNEL = {
    "type": "channel",
    "username": "best_channel_ever",
    "id": -1001065170817,
}

MESSAGE_FROM_CHANNEL = {
    "message_id": 123432,
    "from": None,
    "chat": CHANNEL,
    "date": 1508768405,
    "text": "Hi, world!",
}

PRE_CHECKOUT_QUERY = {
    "id": "262181558630368727",
    "from": USER,
    "currency": "USD",
    "total_amount": 6250,
    "invoice_payload": "HAPPY FRIDAYS COUPON",
}

REPLY_MESSAGE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508751866,
    "reply_to_message": MESSAGE,
    "text": "Reply to quoted message",
}

SHIPPING_QUERY = {
    "id": "262181558684397422",
    "from": USER,
    "invoice_payload": "HAPPY FRIDAYS COUPON",
    "shipping_address": SHIPPING_ADDRESS,
}

USER_PROFILE_PHOTOS = {
    "total_count": 1, "photos": [
        [PHOTO, PHOTO, PHOTO],
    ],
}

FILE = {
    "file_id": "XXXYYYZZZ",
    "file_size": 5254,
    "file_path": "voice/file_8",
}

INVITE_LINK = 'https://t.me/joinchat/AbCdEfjKILDADwdd123'

UPDATE = {
    "update_id": 123456789,
    "message": MESSAGE,
}

WEBHOOK_INFO = {
    "url": "",
    "has_custom_certificate": False,
    "pending_update_count": 0,
}

REPLY_KEYBOARD_MARKUP = {
    "keyboard": [[{"text": "something here"}]],
    "resize_keyboard": True,
}

CHAT_PERMISSIONS = {
    "can_send_messages": True,
    "can_send_media_messages": True,
    "can_send_polls": True,
    "can_send_other_messages": True,
    "can_add_web_page_previews": True,
    "can_change_info": True,
    "can_invite_users": True,
    "can_pin_messages": True,
}

CHAT_LOCATION = {
    "location": LOCATION,
    "address": "address",
}

FULL_CHAT = {
    **CHAT,
    "photo": CHAT_PHOTO,
    "bio": "bio",
    "has_private_forwards": False,
    "description": "description",
    "invite_link": "invite_link",
    "pinned_message": MESSAGE,
    "permissions": CHAT_PERMISSIONS,
    "slow_mode_delay": 10,
    "message_auto_delete_time": 60,
    "has_protected_content": True,
    "sticker_set_name": "sticker_set_name",
    "can_set_sticker_set": True,
    "linked_chat_id": -1234567890,
    "location": CHAT_LOCATION,
}
