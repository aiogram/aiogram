import enum


class ChatAction(str, enum.Enum):
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

    TYPING: str = "typing"                          # typing
    UPLOAD_PHOTO: str = "upload_photo"              # upload_photo
    RECORD_VIDEO: str = "record_video"              # record_video
    UPLOAD_VIDEO: str = "upload_video"              # upload_video
    RECORD_AUDIO: str = "record_audio"              # record_audio
    UPLOAD_AUDIO: str = "upload_audio"              # upload_audio
    RECORD_VOICE: str = "record_voice"              # record_voice
    UPLOAD_VOICE: str = "upload_voice"              # upload_voice
    UPLOAD_DOCUMENT: str = "upload_document"        # upload_document
    FIND_LOCATION: str = "find_location"            # find_location
    RECORD_VIDEO_NOTE: str = "record_video_note"    # record_video_note
    UPLOAD_VIDEO_NOTE: str = "upload_video_note"    # upload_video_note
    CHOOSE_STICKER: str = "choose_sticker"          # choose_sticker
