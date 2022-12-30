import os
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiohttp import ClientResponseError

from aiogram import Bot
from aiogram.types import File
from aiogram.types.mixins import Downloadable
from aiogram.utils.json import json
from tests import TOKEN
from tests.types.dataset import FILE


@pytest_asyncio.fixture(name='bot')
async def bot_fixture():
    """ Bot fixture """
    _bot = Bot(TOKEN)
    yield _bot
    session = await _bot.get_session()
    await session.close()


@pytest.fixture
def tmppath(tmpdir, request):
    os.chdir(tmpdir)
    yield Path(tmpdir)
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def downloadable(bot):
    downloadable = Downloadable()
    downloadable.get_file = AsyncMock(return_value=File(**FILE))
    downloadable.bot = bot

    return downloadable


@pytest.fixture()
def get_file_response(aresponses):
    aresponses.add(response=aresponses.Response(body=json.dumps(FILE)))


class TestDownloadable:
    async def test_download_make_dirs_false_nodir(self, tmppath, downloadable, get_file_response):
        with pytest.raises(FileNotFoundError):
            await downloadable.download(make_dirs=False)

    async def test_download_make_dirs_false_mkdir(self, tmppath, downloadable, get_file_response):
        os.mkdir('voice')
        await downloadable.download(make_dirs=False)
        assert os.path.isfile(tmppath.joinpath(FILE["file_path"]))

    async def test_download_make_dirs_true(self, tmppath, downloadable, get_file_response):
        await downloadable.download(make_dirs=True)
        assert os.path.isfile(tmppath.joinpath(FILE["file_path"]))

    async def test_download_deprecation_warning(self, tmppath, downloadable, get_file_response):
        with pytest.deprecated_call():
            await downloadable.download("test.file")

    async def test_download_destination(self, tmppath, downloadable, get_file_response):
        with pytest.deprecated_call():
            await downloadable.download("test.file")
        assert os.path.isfile(tmppath.joinpath('test.file'))

    async def test_download_destination_dir_exist(self, tmppath, downloadable, get_file_response):
        os.mkdir("test_folder")
        with pytest.deprecated_call():
            await downloadable.download("test_folder")
        assert os.path.isfile(tmppath.joinpath('test_folder', FILE["file_path"]))

    async def test_download_destination_with_dir(self, tmppath, downloadable, get_file_response):
        with pytest.deprecated_call():
            await downloadable.download(os.path.join('dir_name', 'file_name'))
        assert os.path.isfile(tmppath.joinpath('dir_name', 'file_name'))

    async def test_download_destination_io_bytes(self, tmppath, downloadable, get_file_response):
        file = BytesIO()
        with pytest.deprecated_call():
            await downloadable.download(file)
        assert len(file.read()) != 0

    async def test_download_raise_value_error(self, tmppath, downloadable, get_file_response):
        with pytest.raises(ValueError):
            await downloadable.download(destination_dir="a", destination_file="b")

    async def test_download_destination_dir(self, tmppath, downloadable, get_file_response):
        await downloadable.download(destination_dir='test_dir')
        assert os.path.isfile(tmppath.joinpath('test_dir', FILE["file_path"]))

    async def test_download_destination_file(self, tmppath, downloadable, get_file_response):
        await downloadable.download(destination_file='file_name')
        assert os.path.isfile(tmppath.joinpath('file_name'))

    async def test_download_destination_file_with_dir(self, tmppath, downloadable, get_file_response):
        await downloadable.download(destination_file=os.path.join('dir_name', 'file_name'))
        assert os.path.isfile(tmppath.joinpath('dir_name', 'file_name'))

    async def test_download_io_bytes(self, tmppath, downloadable, get_file_response):
        file = BytesIO()
        await downloadable.download(destination_file=file)
        assert len(file.read()) != 0

    async def test_download_404(self, tmppath, downloadable):
        with pytest.raises(ClientResponseError) as exc_info:
            await downloadable.download(destination_file='file_name')

        assert exc_info.value.status == 404
