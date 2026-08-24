import pytest

from aiogram import Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SetStickerKeywords
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.types import BufferedInputFile, InputSticker

PACK = "my_pack_by_test_bot"


def sticker(file_id: str = "file-1", emoji: str = "🐱") -> InputSticker:
    return InputSticker(sticker=file_id, format="static", emoji_list=[emoji])


@pytest.fixture
def packs(dp):
    blueprint = Blueprint()
    owner = blueprint.add_user("Owner")
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield environment, owner
    finally:
        environment.dispose_sync()


class TestTheLifecycle:
    async def test_create_then_add_then_read_back(self, packs):
        env, owner = packs

        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker("file-1")],
        )
        await env.bot.add_sticker_to_set(user_id=owner.id, name=PACK, sticker=sticker("file-2"))

        stored = await env.bot.get_sticker_set(name=PACK)
        assert stored.title == "My pack"
        assert [item.file_id for item in stored.stickers] == ["file-1", "file-2"]

    async def test_a_bot_can_check_a_set_before_writing_to_it(self, packs):
        """The branch this cluster exists to make testable."""
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker("file-1")],
        )

        before = len((await env.bot.get_sticker_set(name=PACK)).stickers)
        await env.bot.add_sticker_to_set(user_id=owner.id, name=PACK, sticker=sticker("file-2"))
        after = len((await env.bot.get_sticker_set(name=PACK)).stickers)

        assert (before, after) == (1, 2)

    async def test_deleting_a_sticker(self, packs):
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker("file-1"), sticker("file-2")],
        )

        await env.bot.delete_sticker_from_set(sticker="file-1")

        stored = await env.bot.get_sticker_set(name=PACK)
        assert [item.file_id for item in stored.stickers] == ["file-2"]

    async def test_replacing_keeps_the_position(self, packs):
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker("file-1"), sticker("file-2"), sticker("file-3")],
        )

        await env.bot.replace_sticker_in_set(
            user_id=owner.id,
            name=PACK,
            old_sticker="file-2",
            sticker=sticker("file-9"),
        )

        stored = await env.bot.get_sticker_set(name=PACK)
        assert [item.file_id for item in stored.stickers] == ["file-1", "file-9", "file-3"]

    async def test_renaming_a_set(self, packs):
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="Old",
            stickers=[sticker()],
        )

        await env.bot.set_sticker_set_title(name=PACK, title="New")

        assert (await env.bot.get_sticker_set(name=PACK)).title == "New"

    async def test_deleting_a_set_removes_it(self, packs):
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker()],
        )

        await env.bot.delete_sticker_set(name=PACK)

        with pytest.raises(TelegramBadRequest, match="does not exist"):
            await env.bot.get_sticker_set(name=PACK)

    async def test_the_sticker_type_is_kept(self, packs):
        env, owner = packs

        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="Emoji",
            sticker_type="custom_emoji",
            stickers=[sticker()],
        )

        assert (await env.bot.get_sticker_set(name=PACK)).sticker_type == "custom_emoji"

    async def test_an_emoji_from_the_input_reaches_the_sticker(self, packs):
        env, owner = packs

        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker("file-1", emoji="🐶")],
        )

        assert (await env.bot.get_sticker_set(name=PACK)).stickers[0].emoji == "🐶"


class TestErrors:
    async def test_a_name_already_taken_fails(self, packs):
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker()],
        )

        with pytest.raises(TelegramBadRequest, match="already occupied"):
            await env.bot.create_new_sticker_set(
                user_id=owner.id,
                name=PACK,
                title="Another",
                stickers=[sticker()],
            )

    @pytest.mark.parametrize(
        ("method_name", "kwargs"),
        [
            ("get_sticker_set", {}),
            ("set_sticker_set_title", {"title": "New"}),
            ("delete_sticker_set", {}),
            ("add_sticker_to_set", {"user_id": 1, "sticker": sticker()}),
            (
                "replace_sticker_in_set",
                {"user_id": 1, "old_sticker": "file-1", "sticker": sticker()},
            ),
        ],
    )
    async def test_an_unknown_set_fails(self, packs, method_name, kwargs):
        env, _ = packs

        with pytest.raises(TelegramBadRequest, match="does not exist"):
            await getattr(env.bot, method_name)(name="no_such_pack", **kwargs)

    async def test_deleting_a_sticker_in_no_set_fails(self, packs):
        env, _ = packs

        with pytest.raises(TelegramBadRequest, match="not in any sticker set"):
            await env.bot.delete_sticker_from_set(sticker="never-added")

    async def test_replacing_a_sticker_the_set_lacks_fails(self, packs):
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker("file-1")],
        )

        with pytest.raises(TelegramBadRequest, match="is not in set"):
            await env.bot.replace_sticker_in_set(
                user_id=owner.id,
                name=PACK,
                old_sticker="not-here",
                sticker=sticker("file-9"),
            )


class TestUploadsAndLookups:
    async def test_an_uploaded_id_can_be_added_to_a_set(self, packs):
        env, owner = packs
        uploaded = await env.bot.upload_sticker_file(
            user_id=owner.id,
            sticker=BufferedInputFile(b"png bytes", filename="cat.png"),
            sticker_format="static",
        )
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker(uploaded.file_id)],
        )

        stored = await env.bot.get_sticker_set(name=PACK)
        assert stored.stickers[0].file_id == uploaded.file_id

    async def test_uploads_are_unique(self, packs):
        env, owner = packs

        first = await env.bot.upload_sticker_file(
            user_id=owner.id,
            sticker=BufferedInputFile(b"png bytes", filename="cat.png"),
            sticker_format="static",
        )
        second = await env.bot.upload_sticker_file(
            user_id=owner.id,
            sticker=BufferedInputFile(b"png bytes", filename="cat.png"),
            sticker_format="static",
        )

        assert first.file_id != second.file_id

    async def test_an_uploaded_sticker_is_not_downloadable(self, packs):
        """Unlike a document upload: a pack bot never downloads its stickers (D4)."""
        import io

        from aiogram.test.errors import NoFileContentError

        env, owner = packs
        uploaded = await env.bot.upload_sticker_file(
            user_id=owner.id,
            sticker=BufferedInputFile(b"png bytes", filename="cat.png"),
            sticker_format="static",
        )

        with pytest.raises(NoFileContentError):
            await env.bot.download(uploaded.file_id, destination=io.BytesIO())

    async def test_custom_emoji_lookups_echo_their_input(self, packs):
        env, _ = packs

        stickers = await env.bot.get_custom_emoji_stickers(custom_emoji_ids=["a", "b"])

        assert [item.custom_emoji_id for item in stickers] == ["a", "b"]
        assert [item.file_id for item in stickers] == ["a", "b"]


class TestDeclaredSets:
    async def test_a_declared_set_is_readable(self, dp):
        blueprint = Blueprint()
        blueprint.add_sticker_set(PACK, "Declared", stickers=3)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            stored = await env.bot.get_sticker_set(name=PACK)

            assert stored.title == "Declared"
            assert len(stored.stickers) == 3
        finally:
            env.dispose_sync()

    async def test_declared_sets_are_isolated_between_environments(self, dp):
        blueprint = Blueprint()
        blueprint.add_sticker_set(PACK, stickers=1)

        first = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        try:
            await first.bot.add_sticker_to_set(user_id=1, name=PACK, sticker=sticker("extra"))

            assert len((await second.bot.get_sticker_set(name=PACK)).stickers) == 1
        finally:
            first.dispose_sync()
            second.dispose_sync()


class TestAttributeSettersStayRecordOnly:
    async def test_setting_keywords_changes_nothing(self, packs):
        env, owner = packs
        await env.bot.create_new_sticker_set(
            user_id=owner.id,
            name=PACK,
            title="My pack",
            stickers=[sticker("file-1")],
        )
        before = await env.bot.get_sticker_set(name=PACK)

        await env.bot.set_sticker_keywords(sticker="file-1", keywords=["cat"])

        assert await env.bot.get_sticker_set(name=PACK) == before
        assert env.calls.count(SetStickerKeywords) == 1
