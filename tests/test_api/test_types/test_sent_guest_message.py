from aiogram.methods import (
    EditMessageCaption,
    EditMessageMedia,
    EditMessageReplyMarkup,
    EditMessageText,
)
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    SentGuestMessage,
)


class TestSentGuestMessage:
    def test_edit_text(self):
        sent_guest_message = SentGuestMessage(inline_message_id="inline_message_id")
        method = sent_guest_message.edit_text(text="test")
        assert isinstance(method, EditMessageText)
        assert method.inline_message_id == sent_guest_message.inline_message_id
        assert method.text == "test"

    def test_edit_caption(self):
        sent_guest_message = SentGuestMessage(inline_message_id="inline_message_id")
        method = sent_guest_message.edit_caption(caption="test")
        assert isinstance(method, EditMessageCaption)
        assert method.inline_message_id == sent_guest_message.inline_message_id
        assert method.caption == "test"

    def test_edit_media(self):
        sent_guest_message = SentGuestMessage(inline_message_id="inline_message_id")
        method = sent_guest_message.edit_media(media=InputMediaPhoto(media="photo.jpg"))
        assert isinstance(method, EditMessageMedia)
        assert method.inline_message_id == sent_guest_message.inline_message_id

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
        sent_guest_message = SentGuestMessage(inline_message_id="inline_message_id")
        method = sent_guest_message.edit_reply_markup(reply_markup=reply_markup)
        assert isinstance(method, EditMessageReplyMarkup)
        assert method.inline_message_id == sent_guest_message.inline_message_id
        assert method.reply_markup == reply_markup
