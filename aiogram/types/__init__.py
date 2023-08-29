from typing import List, Literal, Optional, Union

from .animation import Animation
from .audio import Audio
from .base import UNSET_PARSE_MODE, TelegramObject
from .bot_command import BotCommand
from .bot_command_scope import BotCommandScope
from .bot_command_scope_all_chat_administrators import (
    BotCommandScopeAllChatAdministrators,
)
from .bot_command_scope_all_group_chats import BotCommandScopeAllGroupChats
from .bot_command_scope_all_private_chats import BotCommandScopeAllPrivateChats
from .bot_command_scope_chat import BotCommandScopeChat
from .bot_command_scope_chat_administrators import BotCommandScopeChatAdministrators
from .bot_command_scope_chat_member import BotCommandScopeChatMember
from .bot_command_scope_default import BotCommandScopeDefault
from .bot_description import BotDescription
from .bot_name import BotName
from .bot_short_description import BotShortDescription
from .callback_game import CallbackGame
from .callback_query import CallbackQuery
from .chat import Chat
from .chat_administrator_rights import ChatAdministratorRights
from .chat_invite_link import ChatInviteLink
from .chat_join_request import ChatJoinRequest
from .chat_location import ChatLocation
from .chat_member import ChatMember
from .chat_member_administrator import ChatMemberAdministrator
from .chat_member_banned import ChatMemberBanned
from .chat_member_left import ChatMemberLeft
from .chat_member_member import ChatMemberMember
from .chat_member_owner import ChatMemberOwner
from .chat_member_restricted import ChatMemberRestricted
from .chat_member_updated import ChatMemberUpdated
from .chat_permissions import ChatPermissions
from .chat_photo import ChatPhoto
from .chat_shared import ChatShared
from .chosen_inline_result import ChosenInlineResult
from .contact import Contact
from .custom import DateTime
from .dice import Dice
from .document import Document
from .downloadable import Downloadable
from .encrypted_credentials import EncryptedCredentials
from .encrypted_passport_element import EncryptedPassportElement
from .error_event import ErrorEvent
from .file import File
from .force_reply import ForceReply
from .forum_topic import ForumTopic
from .forum_topic_closed import ForumTopicClosed
from .forum_topic_created import ForumTopicCreated
from .forum_topic_edited import ForumTopicEdited
from .forum_topic_reopened import ForumTopicReopened
from .game import Game
from .game_high_score import GameHighScore
from .general_forum_topic_hidden import GeneralForumTopicHidden
from .general_forum_topic_unhidden import GeneralForumTopicUnhidden
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
from .inline_query_results_button import InlineQueryResultsButton
from .input_contact_message_content import InputContactMessageContent
from .input_file import BufferedInputFile, FSInputFile, InputFile, URLInputFile
from .input_invoice_message_content import InputInvoiceMessageContent
from .input_location_message_content import InputLocationMessageContent
from .input_media import InputMedia
from .input_media_animation import InputMediaAnimation
from .input_media_audio import InputMediaAudio
from .input_media_document import InputMediaDocument
from .input_media_photo import InputMediaPhoto
from .input_media_video import InputMediaVideo
from .input_message_content import InputMessageContent
from .input_sticker import InputSticker
from .input_text_message_content import InputTextMessageContent
from .input_venue_message_content import InputVenueMessageContent
from .invoice import Invoice
from .keyboard_button import KeyboardButton
from .keyboard_button_poll_type import KeyboardButtonPollType
from .keyboard_button_request_chat import KeyboardButtonRequestChat
from .keyboard_button_request_user import KeyboardButtonRequestUser
from .labeled_price import LabeledPrice
from .location import Location
from .login_url import LoginUrl
from .mask_position import MaskPosition
from .menu_button import MenuButton
from .menu_button_commands import MenuButtonCommands
from .menu_button_default import MenuButtonDefault
from .menu_button_web_app import MenuButtonWebApp
from .message import ContentType, Message
from .message_auto_delete_timer_changed import MessageAutoDeleteTimerChanged
from .message_entity import MessageEntity
from .message_id import MessageId
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
from .passport_element_error_translation_files import (
    PassportElementErrorTranslationFiles,
)
from .passport_element_error_unspecified import PassportElementErrorUnspecified
from .passport_file import PassportFile
from .photo_size import PhotoSize
from .poll import Poll
from .poll_answer import PollAnswer
from .poll_option import PollOption
from .pre_checkout_query import PreCheckoutQuery
from .proximity_alert_triggered import ProximityAlertTriggered
from .reply_keyboard_markup import ReplyKeyboardMarkup
from .reply_keyboard_remove import ReplyKeyboardRemove
from .response_parameters import ResponseParameters
from .sent_web_app_message import SentWebAppMessage
from .shipping_address import ShippingAddress
from .shipping_option import ShippingOption
from .shipping_query import ShippingQuery
from .sticker import Sticker
from .sticker_set import StickerSet
from .story import Story
from .successful_payment import SuccessfulPayment
from .switch_inline_query_chosen_chat import SwitchInlineQueryChosenChat
from .update import Update
from .user import User
from .user_profile_photos import UserProfilePhotos
from .user_shared import UserShared
from .venue import Venue
from .video import Video
from .video_chat_ended import VideoChatEnded
from .video_chat_participants_invited import VideoChatParticipantsInvited
from .video_chat_scheduled import VideoChatScheduled
from .video_chat_started import VideoChatStarted
from .video_note import VideoNote
from .voice import Voice
from .web_app_data import WebAppData
from .web_app_info import WebAppInfo
from .webhook_info import WebhookInfo
from .write_access_allowed import WriteAccessAllowed

__all__ = (
    "Animation",
    "Audio",
    "BotCommand",
    "BotCommandScope",
    "BotCommandScopeAllChatAdministrators",
    "BotCommandScopeAllGroupChats",
    "BotCommandScopeAllPrivateChats",
    "BotCommandScopeChat",
    "BotCommandScopeChatAdministrators",
    "BotCommandScopeChatMember",
    "BotCommandScopeDefault",
    "BotDescription",
    "BotName",
    "BotShortDescription",
    "BufferedInputFile",
    "CallbackGame",
    "CallbackQuery",
    "Chat",
    "ChatAdministratorRights",
    "ChatInviteLink",
    "ChatJoinRequest",
    "ChatLocation",
    "ChatMember",
    "ChatMemberAdministrator",
    "ChatMemberBanned",
    "ChatMemberLeft",
    "ChatMemberMember",
    "ChatMemberOwner",
    "ChatMemberRestricted",
    "ChatMemberUpdated",
    "ChatPermissions",
    "ChatPhoto",
    "ChatShared",
    "ChosenInlineResult",
    "Contact",
    "ContentType",
    "DateTime",
    "Dice",
    "Document",
    "Downloadable",
    "EncryptedCredentials",
    "EncryptedPassportElement",
    "ErrorEvent",
    "FSInputFile",
    "File",
    "ForceReply",
    "ForumTopic",
    "ForumTopicClosed",
    "ForumTopicCreated",
    "ForumTopicEdited",
    "ForumTopicReopened",
    "Game",
    "GameHighScore",
    "GeneralForumTopicHidden",
    "GeneralForumTopicUnhidden",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "InlineQuery",
    "InlineQueryResult",
    "InlineQueryResultArticle",
    "InlineQueryResultAudio",
    "InlineQueryResultCachedAudio",
    "InlineQueryResultCachedDocument",
    "InlineQueryResultCachedGif",
    "InlineQueryResultCachedMpeg4Gif",
    "InlineQueryResultCachedPhoto",
    "InlineQueryResultCachedSticker",
    "InlineQueryResultCachedVideo",
    "InlineQueryResultCachedVoice",
    "InlineQueryResultContact",
    "InlineQueryResultDocument",
    "InlineQueryResultGame",
    "InlineQueryResultGif",
    "InlineQueryResultLocation",
    "InlineQueryResultMpeg4Gif",
    "InlineQueryResultPhoto",
    "InlineQueryResultVenue",
    "InlineQueryResultVideo",
    "InlineQueryResultVoice",
    "InlineQueryResultsButton",
    "InputContactMessageContent",
    "InputFile",
    "InputInvoiceMessageContent",
    "InputLocationMessageContent",
    "InputMedia",
    "InputMediaAnimation",
    "InputMediaAudio",
    "InputMediaDocument",
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputMessageContent",
    "InputSticker",
    "InputTextMessageContent",
    "InputVenueMessageContent",
    "Invoice",
    "KeyboardButton",
    "KeyboardButtonPollType",
    "KeyboardButtonRequestChat",
    "KeyboardButtonRequestUser",
    "LabeledPrice",
    "Location",
    "LoginUrl",
    "MaskPosition",
    "MenuButton",
    "MenuButtonCommands",
    "MenuButtonDefault",
    "MenuButtonWebApp",
    "Message",
    "MessageAutoDeleteTimerChanged",
    "MessageEntity",
    "MessageId",
    "OrderInfo",
    "PassportData",
    "PassportElementError",
    "PassportElementErrorDataField",
    "PassportElementErrorFile",
    "PassportElementErrorFiles",
    "PassportElementErrorFrontSide",
    "PassportElementErrorReverseSide",
    "PassportElementErrorSelfie",
    "PassportElementErrorTranslationFile",
    "PassportElementErrorTranslationFiles",
    "PassportElementErrorUnspecified",
    "PassportFile",
    "PhotoSize",
    "Poll",
    "PollAnswer",
    "PollOption",
    "PreCheckoutQuery",
    "ProximityAlertTriggered",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
    "ResponseParameters",
    "SentWebAppMessage",
    "ShippingAddress",
    "ShippingOption",
    "ShippingQuery",
    "Sticker",
    "StickerSet",
    "Story",
    "SuccessfulPayment",
    "SwitchInlineQueryChosenChat",
    "TelegramObject",
    "UNSET_PARSE_MODE",
    "URLInputFile",
    "Update",
    "User",
    "UserProfilePhotos",
    "UserShared",
    "Venue",
    "Video",
    "VideoChatEnded",
    "VideoChatParticipantsInvited",
    "VideoChatScheduled",
    "VideoChatStarted",
    "VideoNote",
    "Voice",
    "WebAppData",
    "WebAppInfo",
    "WebhookInfo",
    "WriteAccessAllowed",
)

# Load typing forward refs for every TelegramObject
for _entity_name in __all__:
    _entity = globals()[_entity_name]
    if not hasattr(_entity, "model_rebuild"):
        continue
    _entity.model_rebuild(
        _types_namespace={
            "List": List,
            "Optional": Optional,
            "Union": Union,
            "Literal": Literal,
            **{k: v for k, v in globals().items() if k in __all__},
        }
    )

del _entity
del _entity_name
