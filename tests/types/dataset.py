""""
Dict data set for Telegram message types
"""

USER = {
    "id": 12345678,
    "is_bot": False,
    "first_name": "FirstName",
    "last_name": "LastName",
    "username": "username",
    "language_code": "ru"
}

CHAT = {
    "id": 12345678,
    "first_name": "FirstName",
    "last_name": "LastName",
    "username": "username",
    "type": "private"
}

PHOTO = {
    "file_id": "AgADBAADFak0G88YZAf8OAug7bHyS9x2ZxkABHVfpJywcloRAAGAAQABAg",
    "file_size": 1101,
    "width": 90,
    "height": 51
}

AUDIO = {
    "duration": 123,
    "mime_type": "audio/mpeg3",
    "file_id": "CQADAgdwadgawd0ChI_rXPyrAg",
    "file_size": 12345678
}

DOCUMENT = {
    "file_name": "test.docx",
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_id": "BQADAgADpgADy_JxS66XQTBRHFleAg",
    "file_size": 21331
}

ANIMATION = {
    "file_name": "a9b0e0ca537aa344338f80978f0896b7.gif.mp4",
    "mime_type": "video/mp4",
    "thumb": PHOTO,
    "file_id": "CgADBAAD4DUAAoceZAe2WiE9y0crrAI",
    "file_size": 65837
}

GAME = {
    "title": "Karate Kido",
    "description": "No trees were harmed in the making of this game :)",
    "photo": [PHOTO, PHOTO, PHOTO],
    "animation": ANIMATION
}

INVOICE = {
    "title": "Working Time Machine",
    "description": "Want to visit your great-great-great-grandparents? "
                   "Make a fortune at the races? "
                   "Shake hands with Hammurabi and take a stroll in the Hanging Gardens? "
                   "Order our Working Time Machine today!",
    "start_parameter": "time-machine-example",
    "currency": "USD",
    "total_amount": 6250
}

LOCATION = {
    "latitude": 55.693416,
    "longitude": 37.624605
}

SHIPPING_ADDRESS = {
    "country_code": "US",
    "state": "State",
    "city": "DefaultCity",
    "street_line1": "Central",
    "street_line2": "Middle",
    "post_code": "424242"
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
    "file_size": 12345
}

SUCCESSFUL_PAYMENT = {
    "currency": "USD",
    "total_amount": 6250,
    "invoice_payload": "HAPPY FRIDAYS COUPON",
    "telegram_payment_charge_id": "_",
    "provider_payment_charge_id": "12345678901234_test"
}

VIDEO = {
    "duration": 52,
    "width": 853,
    "height": 480,
    "mime_type": "video/quicktime",
    "thumb": PHOTO,
    "file_id": "BAADAgpAADdawy_JxS72kRvV3cortAg",
    "file_size": 10099782
}

VOICE = {
    "duration": 1,
    "mime_type": "audio/ogg",
    "file_id": "AwADawAgADADy_JxS2gopIVIIxlhAg",
    "file_size": 4321
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
        "text": "hi there (edited)"
    }

FORWARDED_MESSAGE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508912492,
    "forward_from": USER,
    "forward_date": 1508912176,
    "text": "message text"
}

INLINE_QUERY = {}

MESSAGE = {
    "message_id": 11223,
    "from": USER,
    "chat": CHAT,
    "date": 1508709711,
    "text": "Hi, world!"
}

MESSAGE_WITH_AUDIO = {
        "message_id": 12345,
        "from": USER,
        "chat": CHAT,
        "date": 1508739776,
        "audio": AUDIO
    }

MESSAGE_WITH_AUTHOR_SIGNATURE = {}

MESSAGE_WITH_CHANNEL_CHAT_CREATED = {}

MESSAGE_WITH_CONTACT = {}

MESSAGE_WITH_DELETE_CHAT_PHOTO = {}

MESSAGE_WITH_DOCUMENT = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508768012,
    "document": DOCUMENT,
    "caption": "doc description"
}

MESSAGE_WITH_EDIT_DATE = {}

MESSAGE_WITH_ENTITIES = {}

MESSAGE_WITH_GAME = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508824810,
    "game": GAME
}

MESSAGE_WITH_GROUP_CHAT_CREATED = {}

MESSAGE_WITH_INVOICE = {
    "message_id": 9772,
    "from": USER,
    "chat": CHAT,
    "date": 1508761719,
    "invoice": INVOICE
}

MESSAGE_WITH_LEFT_CHAT_MEMBER = {}

MESSAGE_WITH_LOCATION = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508755473,
    "location": LOCATION
}

MESSAGE_WITH_MIGRATE_FROM_CHAT_ID = {}

MESSAGE_WITH_MIGRATE_TO_CHAT_ID = {}

MESSAGE_WITH_NEW_CHAT_MEMBERS = {}

MESSAGE_WITH_NEW_CHAT_PHOTO = {}

MESSAGE_WITH_NEW_CHAT_TITLE = {}

MESSAGE_WITH_PHOTO = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508825154,
    "photo": [PHOTO, PHOTO, PHOTO, PHOTO],  # 4 sizes of one photo
    "caption": "photo description"
}

MESSAGE_WITH_PINNED_MESSAGE = {}

MESSAGE_WITH_REPLY_TO_MESSAGE = {}

MESSAGE_WITH_STICKER = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508771450,
    "sticker": STICKER
}

MESSAGE_WITH_SUCCESSFUL_PAYMENT = {
    "message_id": 9768,
    "from": USER,
    "chat": CHAT,
    "date": 1508761169,
    "successful_payment": SUCCESSFUL_PAYMENT
}

MESSAGE_WITH_SUPERGROUP_CHAT_CREATED = {}

MESSAGE_WITH_VENUE = {}

MESSAGE_WITH_VIDEO = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508756494,
    "video": VIDEO,
    "caption": "description"
}

MESSAGE_WITH_VIDEO_NOTE = {}

MESSAGE_WITH_VOICE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508768403,
    "voice": VOICE
}

PRE_CHECKOUT_QUERY = {
    "id": "262181558630368727",
    "from": USER,
    "currency": "USD",
    "total_amount": 6250,
    "invoice_payload": "HAPPY FRIDAYS COUPON"
}

REPLY_MESSAGE = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508751866,
    "reply_to_message": MESSAGE,
    "text": "Reply to quoted message"
}

SHIPPING_QUERY = {
    "id": "262181558684397422",
    "from": USER,
    "invoice_payload": "HAPPY FRIDAYS COUPON",
    "shipping_address": SHIPPING_ADDRESS
}

UPDATE = {
    "update_id": 123456789,
    "message": MESSAGE
}
