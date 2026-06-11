from typing import TYPE_CHECKING, Any, Literal

from .base import TelegramObject
from .rich_text import RichText


class RichTextMathematicalExpression(RichText):
    """
    A mathematical expression.

    Source: https://core.telegram.org/bots/api#richtextmathematicalexpression
    """

    type: Literal["mathematical_expression"] = "mathematical_expression"
    """Type of the rich text, always 'mathematical_expression'"""
    expression: str
    """The expression in LaTeX format"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["mathematical_expression"] = "mathematical_expression",
            expression: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, expression=expression, **__pydantic_kwargs)
