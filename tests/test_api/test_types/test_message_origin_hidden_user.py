from aiogram.types import MessageOriginHiddenUser, Update


def test_hidden_user_origin_without_sender_user_name():
    # Telegram omits the documented-as-required `sender_user_name` for legacy
    # forwarded messages reconstructed as `hidden_user` origins; the update
    # must still deserialize instead of failing the whole getUpdates batch.
    # https://github.com/aiogram/aiogram/issues/1840
    raw = {
        "update_id": 1143243230,
        "message": {
            "message_id": 1251,
            "from": {"id": 1, "is_bot": False, "first_name": "A"},
            "chat": {"id": -1002621718979, "type": "supergroup", "title": "T"},
            "date": 1782327884,
            "text": "/purge",
            "reply_to_message": {
                "message_id": 3,
                "from": {"id": 2, "is_bot": False, "first_name": "B"},
                "chat": {"id": -1002621718979, "type": "supergroup", "title": "T"},
                "date": 1422450181,
                "forward_origin": {"type": "hidden_user", "date": 1422450181},
                "forward_date": 1422450181,
                "text": "x",
            },
        },
    }
    update = Update.model_validate(raw)
    origin = update.message.reply_to_message.forward_origin
    assert isinstance(origin, MessageOriginHiddenUser)
    assert origin.sender_user_name is None


def test_hidden_user_origin_with_sender_user_name():
    origin = MessageOriginHiddenUser.model_validate(
        {"type": "hidden_user", "date": 1422450181, "sender_user_name": "anon"}
    )
    assert origin.sender_user_name == "anon"
