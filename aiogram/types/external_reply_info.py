from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .base import TelegramObject

if TYPE_CHECKING:
    from .animation import Animation
    from .audio import Audio
    from .chat import Chat
    from .contact import Contact
    from .dice import Dice
    from .document import Document
    from .game import Game
    from .giveaway import Giveaway
    from .giveaway_winners import GiveawayWinners
    from .invoice import Invoice
    from .link_preview_options import LinkPreviewOptions
    from .location import Location
    from .message_origin_channel import MessageOriginChannel
    from .message_origin_chat import MessageOriginChat
    from .message_origin_hidden_user import MessageOriginHiddenUser
    from .message_origin_user import MessageOriginUser
    from .paid_media_info import PaidMediaInfo
    from .photo_size import PhotoSize
    from .poll import Poll
    from .sticker import Sticker
    from .story import Story
    from .venue import Venue
    from .video import Video
    from .video_note import VideoNote
    from .voice import Voice


class ExternalReplyInfo(TelegramObject):
    """
    This object contains information about a message that is being replied to, which may come from another chat or forum topic.

    Source: https://core.telegram.org/bots/api#externalreplyinfo
    """

    origin: Union[
        MessageOriginUser, MessageOriginHiddenUser, MessageOriginChat, MessageOriginChannel
    ]
    """Origin of the message replied to by the given message"""
    chat: Optional[Chat] = None
    """*Optional*. Chat the original message belongs to. Available only if the chat is a supergroup or a channel."""
    message_id: Optional[int] = None
    """*Optional*. Unique message identifier inside the original chat. Available only if the original chat is a supergroup or a channel."""
    link_preview_options: Optional[LinkPreviewOptions] = None
    """*Optional*. Options used for link preview generation for the original message, if it is a text message"""
    animation: Optional[Animation] = None
    """*Optional*. Message is an animation, information about the animation"""
    audio: Optional[Audio] = None
    """*Optional*. Message is an audio file, information about the file"""
    document: Optional[Document] = None
    """*Optional*. Message is a general file, information about the file"""
    paid_media: Optional[PaidMediaInfo] = None
    """*Optional*. Message contains paid media; information about the paid media"""
    photo: Optional[list[PhotoSize]] = None
    """*Optional*. Message is a photo, available sizes of the photo"""
    sticker: Optional[Sticker] = None
    """*Optional*. Message is a sticker, information about the sticker"""
    story: Optional[Story] = None
    """*Optional*. Message is a forwarded story"""
    video: Optional[Video] = None
    """*Optional*. Message is a video, information about the video"""
    video_note: Optional[VideoNote] = None
    """*Optional*. Message is a `video note <https://telegram.org/blog/video-messages-and-telescope>`_, information about the video message"""
    voice: Optional[Voice] = None
    """*Optional*. Message is a voice message, information about the file"""
    has_media_spoiler: Optional[bool] = None
    """*Optional*. :code:`True`, if the message media is covered by a spoiler animation"""
    contact: Optional[Contact] = None
    """*Optional*. Message is a shared contact, information about the contact"""
    dice: Optional[Dice] = None
    """*Optional*. Message is a dice with random value"""
    game: Optional[Game] = None
    """*Optional*. Message is a game, information about the game. `More about games » <https://core.telegram.org/bots/api#games>`_"""
    giveaway: Optional[Giveaway] = None
    """*Optional*. Message is a scheduled giveaway, information about the giveaway"""
    giveaway_winners: Optional[GiveawayWinners] = None
    """*Optional*. A giveaway with public winners was completed"""
    invoice: Optional[Invoice] = None
    """*Optional*. Message is an invoice for a `payment <https://core.telegram.org/bots/api#payments>`_, information about the invoice. `More about payments » <https://core.telegram.org/bots/api#payments>`_"""
    location: Optional[Location] = None
    """*Optional*. Message is a shared location, information about the location"""
    poll: Optional[Poll] = None
    """*Optional*. Message is a native poll, information about the poll"""
    venue: Optional[Venue] = None
    """*Optional*. Message is a venue, information about the venue"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            origin: Union[
                MessageOriginUser, MessageOriginHiddenUser, MessageOriginChat, MessageOriginChannel
            ],
            chat: Optional[Chat] = None,
            message_id: Optional[int] = None,
            link_preview_options: Optional[LinkPreviewOptions] = None,
            animation: Optional[Animation] = None,
            audio: Optional[Audio] = None,
            document: Optional[Document] = None,
            paid_media: Optional[PaidMediaInfo] = None,
            photo: Optional[list[PhotoSize]] = None,
            sticker: Optional[Sticker] = None,
            story: Optional[Story] = None,
            video: Optional[Video] = None,
            video_note: Optional[VideoNote] = None,
            voice: Optional[Voice] = None,
            has_media_spoiler: Optional[bool] = None,
            contact: Optional[Contact] = None,
            dice: Optional[Dice] = None,
            game: Optional[Game] = None,
            giveaway: Optional[Giveaway] = None,
            giveaway_winners: Optional[GiveawayWinners] = None,
            invoice: Optional[Invoice] = None,
            location: Optional[Location] = None,
            poll: Optional[Poll] = None,
            venue: Optional[Venue] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                origin=origin,
                chat=chat,
                message_id=message_id,
                link_preview_options=link_preview_options,
                animation=animation,
                audio=audio,
                document=document,
                paid_media=paid_media,
                photo=photo,
                sticker=sticker,
                story=story,
                video=video,
                video_note=video_note,
                voice=voice,
                has_media_spoiler=has_media_spoiler,
                contact=contact,
                dice=dice,
                game=game,
                giveaway=giveaway,
                giveaway_winners=giveaway_winners,
                invoice=invoice,
                location=location,
                poll=poll,
                venue=venue,
                **__pydantic_kwargs,
            )
