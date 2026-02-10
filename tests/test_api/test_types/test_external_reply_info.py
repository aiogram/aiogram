from aiogram.types import ExternalReplyInfo


class TestExternalReplyInfo:
    def test_handle_empty_story_accepts_non_dict_values(self):
        value = object()

        assert ExternalReplyInfo.handle_empty_story(value) is value
