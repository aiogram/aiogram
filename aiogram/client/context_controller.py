from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, PrivateAttr
from typing_extensions import Self

if TYPE_CHECKING:
    from aiogram.client.bot import Bot


class BotContextController(BaseModel):
    _bot: Optional["Bot"] = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        self._bot = __context.get("bot") if __context else None

    def as_(self, bot: Optional["Bot"]) -> Self:
        """
        Bind object to a bot instance.

        :param bot: Bot instance
        :return: self
        """
        self._bot = bot
        return self

    @property
    def bot(self) -> Optional["Bot"]:
        """
        Get bot instance.

        :return: Bot instance
        """
        return self._bot
