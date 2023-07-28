from .add_sticker_to_set import AddStickerToSet
from .answer_callback_query import AnswerCallbackQuery
from .answer_inline_query import AnswerInlineQuery
from .answer_pre_checkout_query import AnswerPreCheckoutQuery
from .answer_shipping_query import AnswerShippingQuery
from .answer_web_app_query import AnswerWebAppQuery
from .approve_chat_join_request import ApproveChatJoinRequest
from .ban_chat_member import BanChatMember
from .ban_chat_sender_chat import BanChatSenderChat
from .base import Request, Response, TelegramMethod
from .close import Close
from .close_forum_topic import CloseForumTopic
from .close_general_forum_topic import CloseGeneralForumTopic
from .copy_message import CopyMessage
from .create_chat_invite_link import CreateChatInviteLink
from .create_forum_topic import CreateForumTopic
from .create_invoice_link import CreateInvoiceLink
from .create_new_sticker_set import CreateNewStickerSet
from .decline_chat_join_request import DeclineChatJoinRequest
from .delete_chat_photo import DeleteChatPhoto
from .delete_chat_sticker_set import DeleteChatStickerSet
from .delete_forum_topic import DeleteForumTopic
from .delete_message import DeleteMessage
from .delete_my_commands import DeleteMyCommands
from .delete_sticker_from_set import DeleteStickerFromSet
from .delete_sticker_set import DeleteStickerSet
from .delete_webhook import DeleteWebhook
from .edit_chat_invite_link import EditChatInviteLink
from .edit_forum_topic import EditForumTopic
from .edit_general_forum_topic import EditGeneralForumTopic
from .edit_message_caption import EditMessageCaption
from .edit_message_live_location import EditMessageLiveLocation
from .edit_message_media import EditMessageMedia
from .edit_message_reply_markup import EditMessageReplyMarkup
from .edit_message_text import EditMessageText
from .export_chat_invite_link import ExportChatInviteLink
from .forward_message import ForwardMessage
from .get_chat import GetChat
from .get_chat_administrators import GetChatAdministrators
from .get_chat_member import GetChatMember
from .get_chat_member_count import GetChatMemberCount
from .get_chat_menu_button import GetChatMenuButton
from .get_custom_emoji_stickers import GetCustomEmojiStickers
from .get_file import GetFile
from .get_forum_topic_icon_stickers import GetForumTopicIconStickers
from .get_game_high_scores import GetGameHighScores
from .get_me import GetMe
from .get_my_commands import GetMyCommands
from .get_my_default_administrator_rights import GetMyDefaultAdministratorRights
from .get_my_description import GetMyDescription
from .get_my_name import GetMyName
from .get_my_short_description import GetMyShortDescription
from .get_sticker_set import GetStickerSet
from .get_updates import GetUpdates
from .get_user_profile_photos import GetUserProfilePhotos
from .get_webhook_info import GetWebhookInfo
from .hide_general_forum_topic import HideGeneralForumTopic
from .leave_chat import LeaveChat
from .log_out import LogOut
from .pin_chat_message import PinChatMessage
from .promote_chat_member import PromoteChatMember
from .reopen_forum_topic import ReopenForumTopic
from .reopen_general_forum_topic import ReopenGeneralForumTopic
from .restrict_chat_member import RestrictChatMember
from .revoke_chat_invite_link import RevokeChatInviteLink
from .send_animation import SendAnimation
from .send_audio import SendAudio
from .send_chat_action import SendChatAction
from .send_contact import SendContact
from .send_dice import SendDice
from .send_document import SendDocument
from .send_game import SendGame
from .send_invoice import SendInvoice
from .send_location import SendLocation
from .send_media_group import SendMediaGroup
from .send_message import SendMessage
from .send_photo import SendPhoto
from .send_poll import SendPoll
from .send_sticker import SendSticker
from .send_venue import SendVenue
from .send_video import SendVideo
from .send_video_note import SendVideoNote
from .send_voice import SendVoice
from .set_chat_administrator_custom_title import SetChatAdministratorCustomTitle
from .set_chat_description import SetChatDescription
from .set_chat_menu_button import SetChatMenuButton
from .set_chat_permissions import SetChatPermissions
from .set_chat_photo import SetChatPhoto
from .set_chat_sticker_set import SetChatStickerSet
from .set_chat_title import SetChatTitle
from .set_custom_emoji_sticker_set_thumbnail import SetCustomEmojiStickerSetThumbnail
from .set_game_score import SetGameScore
from .set_my_commands import SetMyCommands
from .set_my_default_administrator_rights import SetMyDefaultAdministratorRights
from .set_my_description import SetMyDescription
from .set_my_name import SetMyName
from .set_my_short_description import SetMyShortDescription
from .set_passport_data_errors import SetPassportDataErrors
from .set_sticker_emoji_list import SetStickerEmojiList
from .set_sticker_keywords import SetStickerKeywords
from .set_sticker_mask_position import SetStickerMaskPosition
from .set_sticker_position_in_set import SetStickerPositionInSet
from .set_sticker_set_thumbnail import SetStickerSetThumbnail
from .set_sticker_set_title import SetStickerSetTitle
from .set_webhook import SetWebhook
from .stop_message_live_location import StopMessageLiveLocation
from .stop_poll import StopPoll
from .unban_chat_member import UnbanChatMember
from .unban_chat_sender_chat import UnbanChatSenderChat
from .unhide_general_forum_topic import UnhideGeneralForumTopic
from .unpin_all_chat_messages import UnpinAllChatMessages
from .unpin_all_forum_topic_messages import UnpinAllForumTopicMessages
from .unpin_chat_message import UnpinChatMessage
from .upload_sticker_file import UploadStickerFile

__all__ = (
    "AddStickerToSet",
    "AnswerCallbackQuery",
    "AnswerInlineQuery",
    "AnswerPreCheckoutQuery",
    "AnswerShippingQuery",
    "AnswerWebAppQuery",
    "ApproveChatJoinRequest",
    "BanChatMember",
    "BanChatSenderChat",
    "Close",
    "CloseForumTopic",
    "CloseGeneralForumTopic",
    "CopyMessage",
    "CreateChatInviteLink",
    "CreateForumTopic",
    "CreateInvoiceLink",
    "CreateNewStickerSet",
    "DeclineChatJoinRequest",
    "DeleteChatPhoto",
    "DeleteChatStickerSet",
    "DeleteForumTopic",
    "DeleteMessage",
    "DeleteMyCommands",
    "DeleteStickerFromSet",
    "DeleteStickerSet",
    "DeleteWebhook",
    "EditChatInviteLink",
    "EditForumTopic",
    "EditGeneralForumTopic",
    "EditMessageCaption",
    "EditMessageLiveLocation",
    "EditMessageMedia",
    "EditMessageReplyMarkup",
    "EditMessageText",
    "ExportChatInviteLink",
    "ForwardMessage",
    "GetChat",
    "GetChatAdministrators",
    "GetChatMember",
    "GetChatMemberCount",
    "GetChatMenuButton",
    "GetCustomEmojiStickers",
    "GetFile",
    "GetForumTopicIconStickers",
    "GetGameHighScores",
    "GetMe",
    "GetMyCommands",
    "GetMyDefaultAdministratorRights",
    "GetMyDescription",
    "GetMyName",
    "GetMyShortDescription",
    "GetStickerSet",
    "GetUpdates",
    "GetUserProfilePhotos",
    "GetWebhookInfo",
    "HideGeneralForumTopic",
    "LeaveChat",
    "LogOut",
    "PinChatMessage",
    "PromoteChatMember",
    "ReopenForumTopic",
    "ReopenGeneralForumTopic",
    "Request",
    "Response",
    "RestrictChatMember",
    "RevokeChatInviteLink",
    "SendAnimation",
    "SendAudio",
    "SendChatAction",
    "SendContact",
    "SendDice",
    "SendDocument",
    "SendGame",
    "SendInvoice",
    "SendLocation",
    "SendMediaGroup",
    "SendMessage",
    "SendPhoto",
    "SendPoll",
    "SendSticker",
    "SendVenue",
    "SendVideo",
    "SendVideoNote",
    "SendVoice",
    "SetChatAdministratorCustomTitle",
    "SetChatDescription",
    "SetChatMenuButton",
    "SetChatPermissions",
    "SetChatPhoto",
    "SetChatStickerSet",
    "SetChatTitle",
    "SetCustomEmojiStickerSetThumbnail",
    "SetGameScore",
    "SetMyCommands",
    "SetMyDefaultAdministratorRights",
    "SetMyDescription",
    "SetMyName",
    "SetMyShortDescription",
    "SetPassportDataErrors",
    "SetStickerEmojiList",
    "SetStickerKeywords",
    "SetStickerMaskPosition",
    "SetStickerPositionInSet",
    "SetStickerSetThumbnail",
    "SetStickerSetTitle",
    "SetWebhook",
    "StopMessageLiveLocation",
    "StopPoll",
    "TelegramMethod",
    "UnbanChatMember",
    "UnbanChatSenderChat",
    "UnhideGeneralForumTopic",
    "UnpinAllChatMessages",
    "UnpinAllForumTopicMessages",
    "UnpinChatMessage",
    "UploadStickerFile",
)
