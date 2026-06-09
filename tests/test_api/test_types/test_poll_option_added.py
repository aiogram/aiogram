from aiogram.types import PollOptionAdded


class TestPollOptionAdded:
    def test_required_fields(self):
        obj = PollOptionAdded(option_persistent_id="opt1", option_text="Option A")
        assert obj.option_persistent_id == "opt1"
        assert obj.option_text == "Option A"
        assert obj.poll_message is None
        assert obj.option_text_entities is None

    def test_optional_fields(self):
        obj = PollOptionAdded(
            option_persistent_id="opt2",
            option_text="Option B",
            option_text_entities=[],
        )
        assert obj.option_text_entities == []
