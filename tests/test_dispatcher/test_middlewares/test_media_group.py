import asyncio

from aiogram.dispatcher.middlewares.media_group import MediaGroupAggregatorMiddleware
from aiogram.types import Message, Chat
from datetime import datetime
from typing import Any
import pytest


class TestMediaGroupAggregatorMiddleware:
    def _get_message(self, message_id: int, **kwargs):
        chat = Chat(id=1, type="private", title="Test")
        return Message(message_id=message_id, date=datetime.now(), chat=chat, **kwargs)

    def get_middleware(self):
        return MediaGroupAggregatorMiddleware(delay=0.1)

    async def test_skip_non_media_group(self):
        is_called = False

        async def next_handler(*args, **kwargs):
            nonlocal is_called
            is_called = True

        await self.get_middleware()(next_handler, self._get_message(1), {})
        assert is_called

    async def test_called_once_for_album(self):
        middleware = self.get_middleware()
        counter = 0
        album = None

        async def next_handler(_, data: dict[str, Any]):
            nonlocal counter, album
            counter += 1
            album = data.get("album")

        await asyncio.gather(
            middleware(next_handler, self._get_message(1, media_group_id="42"), {}),
            middleware(next_handler, self._get_message(2, media_group_id="42"), {}),
        )
        assert album is not None
        assert len(album) == 2
        assert counter == 1

    async def test_propagate_first_media_in_album(self):
        middleware = self.get_middleware()
        first_message = None

        async def next_handler(message: Message, _):
            nonlocal first_message
            first_message = message

        await asyncio.gather(
            middleware(next_handler, self._get_message(2, media_group_id="42"), {}),
            middleware(next_handler, self._get_message(1, media_group_id="42"), {}),
        )
        assert isinstance(first_message, Message)
        assert first_message.message_id == 1

    async def test_different_albums_non_interfere(self):
        middleware = self.get_middleware()
        counter = 0
        albums = []

        async def next_handler(_, data: dict[str, Any]):
            nonlocal counter, albums
            counter += 1
            albums.append(data.get("album"))

        await asyncio.gather(
            middleware(next_handler, self._get_message(1, media_group_id="1"), {}),
            middleware(next_handler, self._get_message(2, media_group_id="2"), {}),
        )
        assert counter == 2
        assert len(albums) == 2

    async def test_retry_handling(self):
        middleware = self.get_middleware()
        album = None

        async def failed_handler(*args, **kwargs):
            raise Exception("Failed")

        async def working_handler(_, data: dict[str, Any]):
            nonlocal album
            album = data.get("album")

        first_message = self._get_message(1, media_group_id="42")
        second_message = self._get_message(2, media_group_id="42")
        with pytest.raises(Exception):
            await asyncio.gather(
                middleware(failed_handler, first_message, {}),
                middleware(failed_handler, second_message, {}),
            )
        await middleware(working_handler, first_message, {})
        assert len(album) == 2
