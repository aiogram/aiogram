from __future__ import annotations

import gettext
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aiogram.utils.i18n.lazy_proxy import LazyProxy
from aiogram.utils.mixins import ContextInstanceMixin

if TYPE_CHECKING:
    from collections.abc import Generator


class I18n(ContextInstanceMixin["I18n"]):
    def __init__(
        self,
        *,
        path: str | Path,
        default_locale: str = "en",
        domain: str = "messages",
    ) -> None:
        self.path = Path(path).resolve()
        self.default_locale = default_locale
        self.domain = domain
        self.ctx_locale = ContextVar("aiogram_ctx_locale", default=default_locale)
        self.locales = self.find_locales()

    @property
    def current_locale(self) -> str:
        return self.ctx_locale.get()

    @current_locale.setter
    def current_locale(self, value: str) -> None:
        self.ctx_locale.set(value)

    @contextmanager
    def use_locale(self, locale: str) -> Generator[None, None, None]:
        """
        Create context with specified locale
        """
        ctx_token = self.ctx_locale.set(locale)
        try:
            yield
        finally:
            self.ctx_locale.reset(ctx_token)

    @contextmanager
    def context(self) -> Generator[I18n, None, None]:
        """
        Use I18n context
        """
        token = self.set_current(self)
        try:
            yield self
        finally:
            self.reset_current(token)

    def find_locales(self) -> dict[str, gettext.GNUTranslations]:
        """
        Load all compiled locales from path

        :return: dict with locales
        """
        translations: dict[str, gettext.GNUTranslations] = {}

        for name in self.path.iterdir():
            if not name.is_dir():
                continue
            mo_path = name / "LC_MESSAGES" / (self.domain + ".mo")

            if mo_path.exists():
                with mo_path.open("rb") as fp:
                    translations[name.name] = gettext.GNUTranslations(fp)
            elif mo_path.with_suffix(".po").exists():  # pragma: no cover
                msg = f"Found locale '{name.name}' but this language is not compiled!"
                raise RuntimeError(msg)

        return translations

    def reload(self) -> None:
        """
        Hot reload locales
        """
        self.locales = self.find_locales()

    @property
    def available_locales(self) -> tuple[str, ...]:
        """
        list of loaded locales

        :return:
        """
        return tuple(self.locales.keys())

    def gettext(
        self,
        singular: str,
        plural: str | None = None,
        n: int = 1,
        locale: str | None = None,
        context: str | None = None,
    ) -> str:
        """
        Get translated text

        :param singular: message id (source string) to translate
        :param plural: plural form of the message id,
            when passed the plural-aware lookup is used
        :param n: number that is used to choose the correct plural form
        :param locale: locale to translate to, current locale is used when omitted
        :param context: message context (gettext :code:`msgctxt`)
            used to disambiguate identical source strings
        :return: translated text
        """
        if locale is None:
            locale = self.current_locale

        if locale not in self.locales:
            if n == 1:
                return singular
            return plural or singular

        translator = self.locales[locale]

        if context is None:
            if plural is None:
                return translator.gettext(singular)
            return translator.ngettext(singular, plural, n)

        if plural is None:
            return translator.pgettext(context, singular)
        return translator.npgettext(context, singular, plural, n)

    def lazy_gettext(
        self,
        singular: str,
        plural: str | None = None,
        n: int = 1,
        locale: str | None = None,
        context: str | None = None,
    ) -> LazyProxy:
        kwargs: dict[str, Any] = {"singular": singular, "plural": plural, "n": n, "locale": locale}
        if context is not None:
            # Forwarded only when set, so subclasses overriding ``gettext``
            # with the pre-context signature keep working
            kwargs["context"] = context
        return LazyProxy(self.gettext, enable_cache=False, **kwargs)
