import os
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiohttp import ClientResponseError

from aiogram import Bot
from aiogram.types import File
from aiogram.utils.json import json
from tests import TOKEN
from tests.types.dataset import FILE


@pytest_asyncio.fixture(name='bot')
async def bot_fixture():
    """ Bot fixture """
    _bot = Bot(TOKEN)
    _bot.get_file = AsyncMock(return_value=File(**FILE))
    yield _bot
    session = await _bot.get_session()
    await session.close()


@pytest.fixture
def file():
    return File(**FILE)


@pytest.fixture
def tmppath(tmpdir, request):
    os.chdir(tmpdir)
    yield Path(tmpdir)
    os.chdir(request.config.invocation_dir)


@pytest.fixture()
def get_file_response(aresponses):
    aresponses.add(response=aresponses.Response(body=json.dumps(FILE)))


class TestBotDownload:
    async def test_download_file(self, tmppath, bot, file, get_file_response):
        f = await bot.download_file(file_path=file.file_path)
        assert len(f.read()) != 0

    async def test_download_file_destination(self, tmppath, bot, file, get_file_response):
        await bot.download_file(file_path=file.file_path, destination="test.file")
        assert os.path.isfile(tmppath.joinpath('test.file'))

    async def test_download_file_destination_with_dir(self, tmppath, bot, file, get_file_response):
        await bot.download_file(file_path=file.file_path,
                                destination=os.path.join('dir_name', 'file_name'))
        assert os.path.isfile(tmppath.joinpath('dir_name', 'file_name'))

    async def test_download_file_destination_raise_file_not_found(self, tmppath, bot, file, get_file_response):
        with pytest.raises(FileNotFoundError):
            await bot.download_file(file_path=file.file_path,
                                    destination=os.path.join('dir_name', 'file_name'),
                                    make_dirs=False)

    async def test_download_file_destination_io_bytes(self, tmppath, bot, file, get_file_response):
        f = BytesIO()
        await bot.download_file(file_path=file.file_path,
                                destination=f)
        assert len(f.read()) != 0

    async def test_download_file_raise_value_error(self, tmppath, bot, file, get_file_response):
        with pytest.raises(ValueError):
            await bot.download_file(file_path=file.file_path, destination="a", destination_dir="b")

    async def test_download_file_destination_dir(self, tmppath, bot, file, get_file_response):
        await bot.download_file(file_path=file.file_path, destination_dir='test_dir')
        assert os.path.isfile(tmppath.joinpath('test_dir', file.file_path))

    async def test_download_file_destination_dir_raise_file_not_found(self, tmppath, bot, file, get_file_response):
        with pytest.raises(FileNotFoundError):
            await bot.download_file(file_path=file.file_path,
                                    destination_dir='test_dir',
                                    make_dirs=False)
            assert os.path.isfile(tmppath.joinpath('test_dir', file.file_path))

    async def test_download_file_404(self, tmppath, bot, file):
        with pytest.raises(ClientResponseError) as exc_info:
            await bot.download_file(file_path=file.file_path)

        assert exc_info.value.status == 404
