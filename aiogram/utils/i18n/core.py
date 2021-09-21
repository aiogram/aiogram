import gettext
import os
from contextvars import ContextVar
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from aiogram.utils.i18n.lazy_proxy import LazyProxy


class I18n:
    def __init__(
        self,
        *,
        path: Union[str, Path],
        locale: str = "en",
        domain: str = "messages",
    ) -> None:
        self.path = path
        self.locale = locale
        self.domain = domain
        self.ctx_locale = ContextVar("aiogram_ctx_locale", default=locale)
        self.locales = self.find_locales()

    @property
    def current_locale(self) -> str:
        return self.ctx_locale.get()

    @current_locale.setter
    def current_locale(self, value: str) -> None:
        self.ctx_locale.set(value)

    def find_locales(self) -> Dict[str, gettext.GNUTranslations]:
        """
        Load all compiled locales from path

        :return: dict with locales
        """
        translations: Dict[str, gettext.GNUTranslations] = {}

        for name in os.listdir(self.path):
            if not os.path.isdir(os.path.join(self.path, name)):
                continue
            mo_path = os.path.join(self.path, name, "LC_MESSAGES", self.domain + ".mo")

            if os.path.exists(mo_path):
                with open(mo_path, "rb") as fp:
                    translations[name] = gettext.GNUTranslations(fp)  # type: ignore
            elif os.path.exists(mo_path[:-2] + "po"):  # pragma: no cover
                raise RuntimeError(f"Found locale '{name}' but this language is not compiled!")

        return translations

    def reload(self) -> None:
        """
        Hot reload locales
        """
        self.locales = self.find_locales()

    @property
    def available_locales(self) -> Tuple[str, ...]:
        """
        list of loaded locales

        :return:
        """
        return tuple(self.locales.keys())

    def gettext(
        self, singular: str, plural: Optional[str] = None, n: int = 1, locale: Optional[str] = None
    ) -> str:
        """
        Get text

        :param singular:
        :param plural:
        :param n:
        :param locale:
        :return:
        """
        if locale is None:
            locale = self.current_locale

        if locale not in self.locales:
            if n == 1:
                return singular
            return plural if plural else singular

        translator = self.locales[locale]

        if plural is None:
            return translator.gettext(singular)
        return translator.ngettext(singular, plural, n)

    def lazy_gettext(
        self, singular: str, plural: Optional[str] = None, n: int = 1, locale: Optional[str] = None
    ) -> LazyProxy:
        return LazyProxy(self.gettext, singular=singular, plural=plural, n=n, locale=locale)
