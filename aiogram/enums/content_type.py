from enum import Enum


class ContentType(str, Enum):
    """
    This object represents a type of content in message
    """

    UNKNOWN = "unknown"
    ANY = "any"
    TEXT = "text"
    ANIMATION = "animation"
    AUDIO = "audio"
    DOCUMENT = "document"
    PAID_MEDIA = "paid_media"
    PHOTO = "photo"
    STICKER = "sticker"
    STORY = "story"
    VIDEO = "video"
    VIDEO_NOTE = "video_note"
    VOICE = "voice"
    CONTACT = "contact"
    DICE = "dice"
    GAME = "game"
    POLL = "poll"
    VENUE = "venue"
    LOCATION = "location"
    NEW_CHAT_MEMBERS = "new_chat_members"
    LEFT_CHAT_MEMBER = "left_chat_member"
    NEW_CHAT_TITLE = "new_chat_title"
    NEW_CHAT_PHOTO = "new_chat_photo"
    DELETE_CHAT_PHOTO = "delete_chat_photo"
    GROUP_CHAT_CREATED = "group_chat_created"
    SUPERGROUP_CHAT_CREATED = "supergroup_chat_created"
    CHANNEL_CHAT_CREATED = "channel_chat_created"
    MESSAGE_AUTO_DELETE_TIMER_CHANGED = "message_auto_delete_timer_changed"
    MIGRATE_TO_CHAT_ID = "migrate_to_chat_id"
    MIGRATE_FROM_CHAT_ID = "migrate_from_chat_id"
    PINNED_MESSAGE = "pinned_message"
    INVOICE = "invoice"
    SUCCESSFUL_PAYMENT = "successful_payment"
    REFUNDED_PAYMENT = "refunded_payment"
    USERS_SHARED = "users_shared"
    CHAT_SHARED = "chat_shared"
    GIFT = "gift"
    UNIQUE_GIFT = "unique_gift"
    CONNECTED_WEBSITE = "connected_website"
    WRITE_ACCESS_ALLOWED = "write_access_allowed"
    PASSPORT_DATA = "passport_data"
    PROXIMITY_ALERT_TRIGGERED = "proximity_alert_triggered"
    BOOST_ADDED = "boost_added"
    CHAT_BACKGROUND_SET = "chat_background_set"
    FORUM_TOPIC_CREATED = "forum_topic_created"
    FORUM_TOPIC_EDITED = "forum_topic_edited"
    FORUM_TOPIC_CLOSED = "forum_topic_closed"
    FORUM_TOPIC_REOPENED = "forum_topic_reopened"
    GENERAL_FORUM_TOPIC_HIDDEN = "general_forum_topic_hidden"
    GENERAL_FORUM_TOPIC_UNHIDDEN = "general_forum_topic_unhidden"
    GIVEAWAY_CREATED = "giveaway_created"
    GIVEAWAY = "giveaway"
    GIVEAWAY_WINNERS = "giveaway_winners"
    GIVEAWAY_COMPLETED = "giveaway_completed"
    PAID_MESSAGE_PRICE_CHANGED = "paid_message_price_changed"
    VIDEO_CHAT_SCHEDULED = "video_chat_scheduled"
    VIDEO_CHAT_STARTED = "video_chat_started"
    VIDEO_CHAT_ENDED = "video_chat_ended"
    VIDEO_CHAT_PARTICIPANTS_INVITED = "video_chat_participants_invited"
    WEB_APP_DATA = "web_app_data"
    USER_SHARED = "user_shared"
