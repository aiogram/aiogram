from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, PrivateAttr
from typing_extensions import Self

if TYPE_CHECKING:
    from aiogram.client.bot import Bot


class BotContextController(BaseModel):
    _bot: Optional["Bot"] = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        self._bot = __context.get("bot") if __context else None

    def get_mounted_bot(self) -> Optional["Bot"]:
        # Properties are not supported in pydantic BaseModel
        # @computed_field decorator is not a solution for this case in due to
        # it produces an additional field in model with validation and serialization that
        # we don't need here
        return self._bot

    def as_(self, bot: Optional["Bot"]) -> Self:
        """
        Bind object to a bot instance.

        :param bot: Bot instance
        :return: self
        """
        self._bot = bot
        return self
