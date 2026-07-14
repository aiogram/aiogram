from enum import Enum


class BotSubscriptionUpdatedState(str, Enum):
    """
    This object contains information about changes to a user payment subscription toward the current bot.

    Source: https://core.telegram.org/bots/api#botsubscriptionupdated
    """

    CANCELED = "canceled"
    ACTIVE = "active"
    FAILED = "failed"
