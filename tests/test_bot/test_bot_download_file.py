import os
from io import BytesIO
from pathlib import Path

import pytest

from aiogram import Bot
from aiogram.types import File
from tests import TOKEN
from tests.types.dataset import FILE

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='bot')
async def bot_fixture():
    async def get_file():
        return File(**FILE)

    """ Bot fixture """
    _bot = Bot(TOKEN)
    _bot.get_file = get_file
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


class TestBotDownload:
    async def test_download_file(self, tmppath, bot, file):
        f = await bot.download_file(file_path=file.file_path)
        assert len(f.read()) != 0

    async def test_download_file_destination(self, tmppath, bot, file):
        await bot.download_file(file_path=file.file_path, destination="test.file")
        assert os.path.isfile(tmppath.joinpath('test.file'))

    async def test_download_file_destination_with_dir(self, tmppath, bot, file):
        await bot.download_file(file_path=file.file_path,
                                destination=os.path.join('dir_name', 'file_name'))
        assert os.path.isfile(tmppath.joinpath('dir_name', 'file_name'))

    async def test_download_file_destination_raise_file_not_found(self, tmppath, bot, file):
        with pytest.raises(FileNotFoundError):
            await bot.download_file(file_path=file.file_path,
                                    destination=os.path.join('dir_name', 'file_name'),
                                    make_dirs=False)

    async def test_download_file_destination_io_bytes(self, tmppath, bot, file):
        f = BytesIO()
        await bot.download_file(file_path=file.file_path,
                                destination=f)
        assert len(f.read()) != 0

    async def test_download_file_raise_value_error(self, tmppath, bot, file):
        with pytest.raises(ValueError):
            await bot.download_file(file_path=file.file_path, destination="a", destination_dir="b")

    async def test_download_file_destination_dir(self, tmppath, bot, file):
        await bot.download_file(file_path=file.file_path, destination_dir='test_dir')
        assert os.path.isfile(tmppath.joinpath('test_dir', file.file_path))

    async def test_download_file_destination_dir_raise_file_not_found(self, tmppath, bot, file):
        with pytest.raises(FileNotFoundError):
            await bot.download_file(file_path=file.file_path,
                                    destination_dir='test_dir',
                                    make_dirs=False)
            assert os.path.isfile(tmppath.joinpath('test_dir', file.file_path))
