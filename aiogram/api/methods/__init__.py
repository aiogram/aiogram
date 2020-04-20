from .add_sticker_to_set import AddStickerToSet
from .answer_callback_query import AnswerCallbackQuery
from .answer_inline_query import AnswerInlineQuery
from .answer_pre_checkout_query import AnswerPreCheckoutQuery
from .answer_shipping_query import AnswerShippingQuery
from .base import Request, Response, TelegramMethod
from .create_new_sticker_set import CreateNewStickerSet
from .delete_chat_photo import DeleteChatPhoto
from .delete_chat_sticker_set import DeleteChatStickerSet
from .delete_message import DeleteMessage
from .delete_sticker_from_set import DeleteStickerFromSet
from .delete_webhook import DeleteWebhook
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
from .get_chat_members_count import GetChatMembersCount
from .get_file import GetFile
from .get_game_high_scores import GetGameHighScores
from .get_me import GetMe
from .get_my_commands import GetMyCommands
from .get_sticker_set import GetStickerSet
from .get_updates import GetUpdates
from .get_user_profile_photos import GetUserProfilePhotos
from .get_webhook_info import GetWebhookInfo
from .kick_chat_member import KickChatMember
from .leave_chat import LeaveChat
from .pin_chat_message import PinChatMessage
from .promote_chat_member import PromoteChatMember
from .restrict_chat_member import RestrictChatMember
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
from .set_chat_permissions import SetChatPermissions
from .set_chat_photo import SetChatPhoto
from .set_chat_sticker_set import SetChatStickerSet
from .set_chat_title import SetChatTitle
from .set_game_score import SetGameScore
from .set_my_commands import SetMyCommands
from .set_passport_data_errors import SetPassportDataErrors
from .set_sticker_position_in_set import SetStickerPositionInSet
from .set_sticker_set_thumb import SetStickerSetThumb
from .set_webhook import SetWebhook
from .stop_message_live_location import StopMessageLiveLocation
from .stop_poll import StopPoll
from .unban_chat_member import UnbanChatMember
from .unpin_chat_message import UnpinChatMessage
from .upload_sticker_file import UploadStickerFile

__all__ = (
    "TelegramMethod",
    "Request",
    "Response",
    "GetUpdates",
    "SetWebhook",
    "DeleteWebhook",
    "GetWebhookInfo",
    "GetMe",
    "SendMessage",
    "ForwardMessage",
    "SendPhoto",
    "SendAudio",
    "SendDocument",
    "SendVideo",
    "SendAnimation",
    "SendVoice",
    "SendVideoNote",
    "SendMediaGroup",
    "SendLocation",
    "EditMessageLiveLocation",
    "StopMessageLiveLocation",
    "SendVenue",
    "SendContact",
    "SendPoll",
    "SendDice",
    "SendChatAction",
    "GetUserProfilePhotos",
    "GetFile",
    "KickChatMember",
    "UnbanChatMember",
    "RestrictChatMember",
    "PromoteChatMember",
    "SetChatAdministratorCustomTitle",
    "SetChatPermissions",
    "ExportChatInviteLink",
    "SetChatPhoto",
    "DeleteChatPhoto",
    "SetChatTitle",
    "SetChatDescription",
    "PinChatMessage",
    "UnpinChatMessage",
    "LeaveChat",
    "GetChat",
    "GetChatAdministrators",
    "GetChatMembersCount",
    "GetChatMember",
    "SetChatStickerSet",
    "DeleteChatStickerSet",
    "AnswerCallbackQuery",
    "SetMyCommands",
    "GetMyCommands",
    "EditMessageText",
    "EditMessageCaption",
    "EditMessageMedia",
    "EditMessageReplyMarkup",
    "StopPoll",
    "DeleteMessage",
    "SendSticker",
    "GetStickerSet",
    "UploadStickerFile",
    "CreateNewStickerSet",
    "AddStickerToSet",
    "SetStickerPositionInSet",
    "DeleteStickerFromSet",
    "SetStickerSetThumb",
    "AnswerInlineQuery",
    "SendInvoice",
    "AnswerShippingQuery",
    "AnswerPreCheckoutQuery",
    "SetPassportDataErrors",
    "SendGame",
    "SetGameScore",
    "GetGameHighScores",
)
