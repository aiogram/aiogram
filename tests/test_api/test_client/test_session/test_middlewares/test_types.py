from textwrap import dedent

import pytest


def test_request_middleware_result_types(tmp_path):
    mypy_api = pytest.importorskip("mypy.api")
    source = tmp_path / "middleware_types.py"
    source.write_text(
        dedent(
            """
            from typing_extensions import assert_type

            from aiogram import Bot
            from aiogram.client.session.base import BaseSession
            from aiogram.client.session.middlewares.base import (
                BaseRequestMiddleware,
                NextRequestMiddlewareType,
                RequestMiddlewareType,
            )
            from aiogram.client.session.middlewares.request_logging import RequestLogging
            from aiogram.methods import DeleteWebhook, GetMe, TelegramMethod
            from aiogram.methods.base import TelegramType
            from aiogram.types import User


            class Middleware(BaseRequestMiddleware):
                async def __call__(
                    self,
                    make_request: NextRequestMiddlewareType[TelegramType],
                    bot: Bot,
                    method: TelegramMethod[TelegramType],
                ) -> TelegramType:
                    return await make_request(bot, method)


            async def check_middleware_types(
                bot: Bot, session: BaseSession, base_middleware: BaseRequestMiddleware
            ) -> None:
                middleware: RequestMiddlewareType = Middleware()
                session.middleware.register(middleware)
                session.middleware.register(RequestLogging())

                get_me: NextRequestMiddlewareType[User] = session.make_request
                assert_type(await get_me(bot, GetMe()), User)
                assert_type(await middleware(get_me, bot, GetMe()), User)
                assert_type(await base_middleware(get_me, bot, GetMe()), User)
                assert_type(await RequestLogging()(get_me, bot, GetMe()), User)

                delete_webhook: NextRequestMiddlewareType[bool] = session.make_request
                assert_type(await delete_webhook(bot, DeleteWebhook()), bool)
                assert_type(await middleware(delete_webhook, bot, DeleteWebhook()), bool)
                assert_type(await base_middleware(delete_webhook, bot, DeleteWebhook()), bool)
                assert_type(await RequestLogging()(delete_webhook, bot, DeleteWebhook()), bool)
            """
        ),
        encoding="utf-8",
    )

    stdout, stderr, status = mypy_api.run(
        ["--follow-imports=silent", "--cache-dir", str(tmp_path / "mypy_cache"), str(source)]
    )

    assert status == 0, stdout + stderr
