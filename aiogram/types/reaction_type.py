from .base import TelegramObject


class ReactionType(TelegramObject):
    """
    This object describes the type of a reaction. Currently, it can be one of

     - :class:`aiogram.types.reaction_type_emoji.ReactionTypeEmoji`
     - :class:`aiogram.types.reaction_type_custom_emoji.ReactionTypeCustomEmoji`

    Source: https://core.telegram.org/bots/api#reactiontype
    """
