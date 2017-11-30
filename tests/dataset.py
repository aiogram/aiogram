USER = {
    "id": 12345678,
    "is_bot": False,
    "first_name": "FirstName",
    "last_name": "LastName",
    "username": "username",
    "language_code": "ru-RU"
}

CHAT = {
    "id": 12345678,
    "first_name": "FirstName",
    "last_name": "LastName",
    "username": "username",
    "type": "private"
}

MESSAGE = {
    "message_id": 11223,
    "from": USER,
    "chat": CHAT,
    "date": 1508709711,
    "text": "Hi, world!"
}

DOCUMENT = {
    "file_name": "test.docx",
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_id": "BQADAgADpgADy_JxS66XQTBRHFleAg",
    "file_size": 21331
}

MESSAGE_WITH_DOCUMENT = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508768012,
    "document": DOCUMENT,
    "caption": "doc description"
}

UPDATE = {
    "update_id": 128526,
    "message": MESSAGE
}

PHOTO = {
    "file_id": "AgADBAADFak0G88YZAf8OAug7bHyS9x2ZxkABHVfpJywcloRAAGAAQABAg",
    "file_size": 1101,
    "width": 90,
    "height": 51
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

MESSAGE_WITH_GAME = {
    "message_id": 12345,
    "from": USER,
    "chat": CHAT,
    "date": 1508824810,
    "game": GAME
}
