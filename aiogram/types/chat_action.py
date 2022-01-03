from ..utils import helper


class ChatAction(helper.Helper):
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

    mode = helper.HelperMode.snake_case

    TYPING: str = helper.Item()             # typing
    UPLOAD_PHOTO: str = helper.Item()       # upload_photo
    RECORD_VIDEO: str = helper.Item()       # record_video
    UPLOAD_VIDEO: str = helper.Item()       # upload_video
    RECORD_AUDIO: str = helper.Item()       # record_audio
    UPLOAD_AUDIO: str = helper.Item()       # upload_audio
    RECORD_VOICE: str = helper.Item()       # record_voice
    UPLOAD_VOICE: str = helper.Item()       # upload_voice
    UPLOAD_DOCUMENT: str = helper.Item()    # upload_document
    FIND_LOCATION: str = helper.Item()      # find_location
    RECORD_VIDEO_NOTE: str = helper.Item()  # record_video_note
    UPLOAD_VIDEO_NOTE: str = helper.Item()  # upload_video_note
    CHOOSE_STICKER: str = helper.Item()     # choose_sticker
