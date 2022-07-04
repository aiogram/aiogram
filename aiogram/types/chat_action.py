import enum

from ..utils.enum import AutoName


class ChatAction(AutoName):
    """
    This object represents bot actions.

    Choose one, depending on what the user is about to receive:
        • typing for text messages,
        • upload_photo for photos,
        • record_video or upload_video for videos,
        • record_voice or upload_voice for voice notes,
        • upload_document for general files,
        • choose_sticker for stickers,
        • find_location for location data,
        • record_video_note or upload_video_note for video notes.

    Source: https://core.telegram.org/bots/api#sendchataction
    """

    TYPING = enum.auto()
    UPLOAD_PHOTO = enum.auto()
    RECORD_VIDEO = enum.auto()
    UPLOAD_VIDEO = enum.auto()
    RECORD_VOICE = enum.auto()
    UPLOAD_VOICE = enum.auto()
    UPLOAD_DOCUMENT = enum.auto()
    CHOOSE_STICKER = enum.auto()
    FIND_LOCATION = enum.auto()
    RECORD_VIDEO_NOTE = enum.auto()
    UPLOAD_VIDEO_NOTE = enum.auto()
