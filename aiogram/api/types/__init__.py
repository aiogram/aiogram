from .animation import Animation
from .audio import Audio
from .base import TelegramObject
from .callback_game import CallbackGame
from .callback_query import CallbackQuery
from .chat import Chat
from .chat_member import ChatMember
from .chat_permissions import ChatPermissions
from .chat_photo import ChatPhoto
from .chosen_inline_result import ChosenInlineResult
from .contact import Contact
from .document import Document
from .encrypted_credentials import EncryptedCredentials
from .encrypted_passport_element import EncryptedPassportElement
from .file import File
from .force_reply import ForceReply
from .game import Game
from .game_high_score import GameHighScore
from .inline_keyboard_button import InlineKeyboardButton
from .inline_keyboard_markup import InlineKeyboardMarkup
from .inline_query import InlineQuery
from .inline_query_result import InlineQueryResult
from .inline_query_result_article import InlineQueryResultArticle
from .inline_query_result_audio import InlineQueryResultAudio
from .inline_query_result_cached_audio import InlineQueryResultCachedAudio
from .inline_query_result_cached_document import InlineQueryResultCachedDocument
from .inline_query_result_cached_gif import InlineQueryResultCachedGif
from .inline_query_result_cached_mpeg4_gif import InlineQueryResultCachedMpeg4Gif
from .inline_query_result_cached_photo import InlineQueryResultCachedPhoto
from .inline_query_result_cached_sticker import InlineQueryResultCachedSticker
from .inline_query_result_cached_video import InlineQueryResultCachedVideo
from .inline_query_result_cached_voice import InlineQueryResultCachedVoice
from .inline_query_result_contact import InlineQueryResultContact
from .inline_query_result_document import InlineQueryResultDocument
from .inline_query_result_game import InlineQueryResultGame
from .inline_query_result_gif import InlineQueryResultGif
from .inline_query_result_location import InlineQueryResultLocation
from .inline_query_result_mpeg4_gif import InlineQueryResultMpeg4Gif
from .inline_query_result_photo import InlineQueryResultPhoto
from .inline_query_result_venue import InlineQueryResultVenue
from .inline_query_result_video import InlineQueryResultVideo
from .inline_query_result_voice import InlineQueryResultVoice
from .input_contact_message_content import InputContactMessageContent
from .input_file import InputFile
from .input_location_message_content import InputLocationMessageContent
from .input_media import InputMedia
from .input_media_animation import InputMediaAnimation
from .input_media_audio import InputMediaAudio
from .input_media_document import InputMediaDocument
from .input_media_photo import InputMediaPhoto
from .input_media_video import InputMediaVideo
from .input_message_content import InputMessageContent
from .input_text_message_content import InputTextMessageContent
from .input_venue_message_content import InputVenueMessageContent
from .invoice import Invoice
from .keyboard_button import KeyboardButton
from .labeled_price import LabeledPrice
from .location import Location
from .login_url import LoginUrl
from .mask_position import MaskPosition
from .message import Message
from .message_entity import MessageEntity
from .order_info import OrderInfo
from .passport_data import PassportData
from .passport_element_error import PassportElementError
from .passport_element_error_data_field import PassportElementErrorDataField
from .passport_element_error_file import PassportElementErrorFile
from .passport_element_error_files import PassportElementErrorFiles
from .passport_element_error_front_side import PassportElementErrorFrontSide
from .passport_element_error_reverse_side import PassportElementErrorReverseSide
from .passport_element_error_selfie import PassportElementErrorSelfie
from .passport_element_error_translation_file import PassportElementErrorTranslationFile
from .passport_element_error_translation_files import PassportElementErrorTranslationFiles
from .passport_element_error_unspecified import PassportElementErrorUnspecified
from .passport_file import PassportFile
from .photo_size import PhotoSize
from .poll import Poll
from .poll_option import PollOption
from .pre_checkout_query import PreCheckoutQuery
from .reply_keyboard_markup import ReplyKeyboardMarkup
from .reply_keyboard_remove import ReplyKeyboardRemove
from .response_parameters import ResponseParameters
from .shipping_address import ShippingAddress
from .shipping_option import ShippingOption
from .shipping_query import ShippingQuery
from .sticker import Sticker
from .sticker_set import StickerSet
from .successful_payment import SuccessfulPayment
from .update import Update
from .user import User
from .user_profile_photos import UserProfilePhotos
from .venue import Venue
from .video import Video
from .video_note import VideoNote
from .voice import Voice
from .webhook_info import WebhookInfo

__all__ = (
    "TelegramObject",
    "InputFile",
    "Update",
    "WebhookInfo",
    "User",
    "Chat",
    "Message",
    "MessageEntity",
    "PhotoSize",
    "Audio",
    "Document",
    "Video",
    "Animation",
    "Voice",
    "VideoNote",
    "Contact",
    "Location",
    "Venue",
    "PollOption",
    "Poll",
    "UserProfilePhotos",
    "File",
    "ReplyKeyboardMarkup",
    "KeyboardButton",
    "ReplyKeyboardRemove",
    "InlineKeyboardMarkup",
    "InlineKeyboardButton",
    "LoginUrl",
    "CallbackQuery",
    "ForceReply",
    "ChatPhoto",
    "ChatMember",
    "ChatPermissions",
    "ResponseParameters",
    "InputMedia",
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputMediaAnimation",
    "InputMediaAudio",
    "InputMediaDocument",
    "Sticker",
    "StickerSet",
    "MaskPosition",
    "InlineQuery",
    "InlineQueryResult",
    "InlineQueryResultArticle",
    "InlineQueryResultPhoto",
    "InlineQueryResultGif",
    "InlineQueryResultMpeg4Gif",
    "InlineQueryResultVideo",
    "InlineQueryResultAudio",
    "InlineQueryResultVoice",
    "InlineQueryResultDocument",
    "InlineQueryResultLocation",
    "InlineQueryResultVenue",
    "InlineQueryResultContact",
    "InlineQueryResultGame",
    "InlineQueryResultCachedPhoto",
    "InlineQueryResultCachedGif",
    "InlineQueryResultCachedMpeg4Gif",
    "InlineQueryResultCachedSticker",
    "InlineQueryResultCachedDocument",
    "InlineQueryResultCachedVideo",
    "InlineQueryResultCachedVoice",
    "InlineQueryResultCachedAudio",
    "InputMessageContent",
    "InputTextMessageContent",
    "InputLocationMessageContent",
    "InputVenueMessageContent",
    "InputContactMessageContent",
    "ChosenInlineResult",
    "LabeledPrice",
    "Invoice",
    "ShippingAddress",
    "OrderInfo",
    "ShippingOption",
    "SuccessfulPayment",
    "ShippingQuery",
    "PreCheckoutQuery",
    "PassportData",
    "PassportFile",
    "EncryptedPassportElement",
    "EncryptedCredentials",
    "PassportElementError",
    "PassportElementErrorDataField",
    "PassportElementErrorFrontSide",
    "PassportElementErrorReverseSide",
    "PassportElementErrorSelfie",
    "PassportElementErrorFile",
    "PassportElementErrorFiles",
    "PassportElementErrorTranslationFile",
    "PassportElementErrorTranslationFiles",
    "PassportElementErrorUnspecified",
    "Game",
    "CallbackGame",
    "GameHighScore",
)

# Load typing forward refs for every TelegramObject
for entity in __all__[2:]:
    globals()[entity].update_forward_refs(**globals())
