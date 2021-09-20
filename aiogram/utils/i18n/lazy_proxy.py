from typing import Any

try:
    from babel.support import LazyProxy
except ImportError:  # pragma: no cover

    class LazyProxy:  # type: ignore
        def __init__(self, func: Any, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "LazyProxy can be used only when Babel installed\n"
                "Just install Babel (`pip install Babel`) "
                "or aiogram with i18n support (`pip install aiogram[i18n]`)"
            )
