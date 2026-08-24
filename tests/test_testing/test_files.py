import io
import pathlib

import pytest

from aiogram import Dispatcher
from aiogram.methods import GetFile
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.test.errors import NoFileContentError
from aiogram.types import BufferedInputFile, File, FSInputFile, URLInputFile

CONTENT = b"the quick brown fox" * 10


@pytest.fixture
def files_env(dp):
    blueprint = Blueprint()
    user = blueprint.add_user("Ann")
    chat = blueprint.add_private_chat(user)
    blueprint.add_file("declared-id", CONTENT)
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield environment, environment.chat(chat)
    finally:
        environment.dispose_sync()


async def download(bot, target):
    buffer = io.BytesIO()
    await bot.download(target, destination=buffer)
    return buffer.getvalue()


class TestDeclaredContent:
    async def test_a_declared_file_downloads_its_content(self, files_env):
        env, _ = files_env

        assert await download(env.bot, "declared-id") == CONTENT

    async def test_get_file_reports_the_size_of_the_content(self, files_env):
        env, _ = files_env

        file = await env.bot.get_file(file_id="declared-id")

        assert file.file_size == len(CONTENT)
        assert file.file_id == "declared-id"

    async def test_content_is_chunked_rather_than_truncated(self, files_env):
        """A file larger than one chunk still arrives whole."""
        env, _ = files_env
        buffer = io.BytesIO()

        await env.bot.download("declared-id", destination=buffer, chunk_size=8)

        assert buffer.getvalue() == CONTENT

    async def test_declared_content_is_isolated_between_environments(self, blueprint):
        blueprint.add_file("shared-id", b"original")
        first = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        try:
            first.world.files["shared-id"] = b"changed"

            assert await download(second.bot, "shared-id") == b"original"
        finally:
            first.dispose_sync()
            second.dispose_sync()


class TestUploadedContent:
    async def test_upload_then_download_round_trips(self, files_env):
        env, chat = files_env

        message = await env.bot.send_document(
            chat_id=chat.id,
            document=BufferedInputFile(b"uploaded bytes", filename="notes.txt"),
        )

        assert await download(env.bot, message.document) == b"uploaded bytes"

    async def test_downloading_by_file_id_works_too(self, files_env):
        env, chat = files_env
        message = await env.bot.send_document(
            chat_id=chat.id,
            document=BufferedInputFile(b"uploaded bytes", filename="notes.txt"),
        )

        assert await download(env.bot, message.document.file_id) == b"uploaded bytes"

    async def test_a_photo_upload_registers_its_first_size(self, files_env):
        """``Message.photo`` is a list; the registered id is the one a test can reach."""
        env, chat = files_env

        message = await env.bot.send_photo(
            chat_id=chat.id,
            photo=BufferedInputFile(b"image bytes", filename="cat.jpg"),
        )

        assert await download(env.bot, message.photo[0]) == b"image bytes"

    async def test_a_plain_file_id_send_registers_nothing(self, files_env):
        """Sending by file id uploads no bytes, so there is nothing to download."""
        env, chat = files_env

        message = await env.bot.send_document(chat_id=chat.id, document="some-remote-id")

        with pytest.raises(NoFileContentError):
            await download(env.bot, message.document)


class TestMissingContentFailsLoudly:
    async def test_downloading_undeclared_content_raises(self, files_env):
        """The regression: this used to succeed and hand back ``b''``."""
        env, _ = files_env

        with pytest.raises(NoFileContentError, match="No content is registered"):
            await download(env.bot, "never-declared")

    async def test_the_error_names_the_file_and_both_escapes(self, files_env):
        env, _ = files_env

        with pytest.raises(NoFileContentError) as info:
            await download(env.bot, "never-declared")

        message = str(info.value)
        assert "never-declared" in message
        assert "add_file" in message
        assert "env.on(GetFile).returns" in message

    async def test_the_error_surfaces_through_download_file(self, files_env):
        env, _ = files_env
        file = await env.bot.get_file(file_id="never-declared")

        with pytest.raises(NoFileContentError):
            await env.bot.download_file(file.file_path, destination=io.BytesIO())

    async def test_a_failed_download_does_not_leave_an_empty_destination(self, files_env):
        env, _ = files_env
        destination = io.BytesIO()

        with pytest.raises(NoFileContentError):
            await env.bot.download("never-declared", destination=destination)

        assert destination.getvalue() == b""

    @pytest.mark.parametrize(
        "input_file",
        [
            pytest.param(FSInputFile(pathlib.Path(__file__)), id="FSInputFile"),
            pytest.param(URLInputFile("https://example.org/x.txt"), id="URLInputFile"),
        ],
    )
    async def test_inputs_backed_by_disk_or_network_are_never_read(self, files_env, input_file):
        """A test environment must not touch the filesystem or the network."""
        env, chat = files_env

        message = await env.bot.send_document(chat_id=chat.id, document=input_file)

        with pytest.raises(NoFileContentError):
            await download(env.bot, message.document)


class TestGetFileRemainsForgiving:
    async def test_get_file_succeeds_without_content(self, files_env):
        """A bot often reads the path or size and never downloads — see design D2."""
        env, _ = files_env

        file = await env.bot.get_file(file_id="never-declared")

        assert isinstance(file, File)
        assert file.file_id == "never-declared"

    async def test_an_override_still_wins(self, files_env):
        env, _ = files_env
        env.on(GetFile).returns(File(file_id="x", file_unique_id="u", file_path="declared-id"))

        file = await env.bot.get_file(file_id="ignored")

        assert file.file_path == "declared-id"
