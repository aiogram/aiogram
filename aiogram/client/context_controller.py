from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, PrivateAttr
from typing_extensions import Self

if TYPE_CHECKING:
    from aiogram.client.bot import Bot


class BotContextController(BaseModel):
    _bot: Optional["Bot"] = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        if not __context:
            self._bot = None
        else:
            self._bot = __context.get("bot")

    def as_(self, bot: "Bot") -> Self:
        """Bind object to a bot instance."""
        self._bot = bot
        return self
