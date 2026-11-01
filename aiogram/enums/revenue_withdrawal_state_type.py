from enum import StrEnum


class RevenueWithdrawalStateType(StrEnum):
    """
    This object represents a revenue withdrawal state type

    Source: https://core.telegram.org/bots/api#revenuewithdrawalstate
    """

    FAILED = "failed"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
