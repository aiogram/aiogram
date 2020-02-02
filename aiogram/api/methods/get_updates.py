from typing import Any, Dict, List, Optional

from ..types import Update
from .base import Request, TelegramMethod


class GetUpdates(TelegramMethod[List[Update]]):
    """
    Use this method to receive incoming updates using long polling (wiki). An Array of Update
    objects is returned.
    Notes
    1. This method will not work if an outgoing webhook is set up.
    2. In order to avoid getting duplicate updates, recalculate offset after each server response.

    Source: https://core.telegram.org/bots/api#getupdates
    """

    __returning__ = List[Update]

    offset: Optional[int] = None
    """Identifier of the first update to be returned. Must be greater by one than the highest
    among the identifiers of previously received updates. By default, updates starting with the
    earliest unconfirmed update are returned. An update is considered confirmed as soon as
    getUpdates is called with an offset higher than its update_id. The negative offset can be
    specified to retrieve updates starting from -offset update from the end of the updates
    queue. All previous updates will forgotten."""
    limit: Optional[int] = None
    """Limits the number of updates to be retrieved. Values between 1—100 are accepted. Defaults
    to 100."""
    timeout: Optional[int] = None
    """Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be
    positive, short polling should be used for testing purposes only."""
    allowed_updates: Optional[List[str]] = None
    """A JSON-serialized list of the update types you want your bot to receive. For example,
    specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of
    these types. See Update for a complete list of available update types. Specify an empty
    list to receive all updates regardless of type (default). If not specified, the previous
    setting will be used."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getUpdates", data=data)
