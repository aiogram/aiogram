import os
import shutil
from io import BytesIO
from pathlib import Path

import pytest

from aiogram import Bot
from aiogram.types import File
from aiogram.types.mixins import Downloadable
from tests import TOKEN
from tests.types.dataset import FILE

DIR_NAME = 'downloadable_tests'
DIR = Path.joinpath(Path(__file__).parent, DIR_NAME)

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='bot')
async def bot_fixture():
    """ Bot fixture """
    _bot = Bot(TOKEN)
    yield _bot
    await _bot.session.close()


@pytest.fixture
def work_directory(request):
    os.makedirs(DIR, exist_ok=True)
    os.chdir(Path.joinpath(Path(request.fspath.dirname), DIR_NAME))
    yield DIR
    os.chdir(request.config.invocation_dir)
    shutil.rmtree(DIR)


@pytest.fixture
def downloadable(bot):
    async def get_file():
        return File(**FILE)

    downloadable = Downloadable()
    downloadable.get_file = get_file
    downloadable.bot = bot

    return downloadable


class TestDownloadable:
    async def test_download_make_dirs_false_nodir(self, work_directory, downloadable):
        with pytest.raises(FileNotFoundError):
            await downloadable.download(make_dirs=False)

    async def test_download_make_dirs_false_mkdir(self, work_directory, downloadable):
        os.mkdir('voice')
        await downloadable.download(make_dirs=False)
        assert os.path.isfile(work_directory.joinpath(FILE["file_path"]))

    async def test_download_make_dirs_true(self, work_directory, downloadable):
        await downloadable.download(make_dirs=True)
        assert os.path.isfile(work_directory.joinpath(FILE["file_path"]))

    async def test_download_deprecation_warning(self, work_directory, downloadable):
        with pytest.deprecated_call():
            await downloadable.download("test.file")

    async def test_download_destination(self, work_directory, downloadable):
        with pytest.deprecated_call():
            await downloadable.download("test.file")
        assert os.path.isfile(work_directory.joinpath('test.file'))

    async def test_download_destination_dir_exist(self, work_directory, downloadable):
        os.mkdir("test_folder")
        with pytest.deprecated_call():
            await downloadable.download("test_folder")
        assert os.path.isfile(work_directory.joinpath('test_folder', FILE["file_path"]))

    async def test_download_destination_with_dir(self, work_directory, downloadable):
        with pytest.deprecated_call():
            await downloadable.download(os.path.join('dir_name', 'file_name'))
        assert os.path.isfile(work_directory.joinpath(os.path.join('dir_name', 'file_name')))

    async def test_download_destination_io_bytes(self, work_directory, downloadable):
        file = BytesIO()
        await downloadable.download(file)
        assert len(file.read()) != 0

    async def test_download_raise_value_error(self, work_directory, downloadable):
        with pytest.raises(ValueError):
            await downloadable.download(destination_dir="a", destination_file="b")

    async def test_download_destination_dir(self, work_directory, downloadable):
        await downloadable.download(destination_dir='test_dir')
        assert os.path.isfile(work_directory.joinpath('test_dir', FILE["file_path"]))

    async def test_download_destination_file(self, work_directory, downloadable):
        await downloadable.download(destination_file='file_name')
        assert os.path.isfile(work_directory.joinpath('file_name'))

    async def test_download_destination_file_with_dir(self, work_directory, downloadable):
        await downloadable.download(destination_file=os.path.join('dir_name', 'file_name'))
        assert os.path.isfile(work_directory.joinpath('dir_name', 'file_name'))

    async def test_download_io_bytes(self, work_directory, downloadable):
        file = BytesIO()
        await downloadable.download(destination_file=file)
        assert len(file.read()) != 0
