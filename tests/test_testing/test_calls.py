import pytest

from aiogram.methods import DeleteMessage, EditMessageText, SendMessage
from aiogram.test import CallLog, NoSuchCallError


def send(chat_id: int, text: str) -> SendMessage:
    return SendMessage(chat_id=chat_id, text=text)


class TestCallLog:
    def test_records_in_order(self):
        log = CallLog()
        log.record(send(1, "a"))
        log.record(send(1, "b"))

        assert [item.text for item in log.all(SendMessage)] == ["a", "b"]
        assert log.entries[0].text == "a"

    def test_first_and_last(self):
        log = CallLog()
        log.record(send(1, "a"))
        log.record(send(1, "b"))

        assert log.first(SendMessage).text == "a"
        assert log.last(SendMessage).text == "b"

    def test_count(self):
        log = CallLog()
        log.record(send(1, "a"))
        log.record(DeleteMessage(chat_id=1, message_id=1))

        assert log.count() == 2
        assert log.count(SendMessage) == 1
        assert log.count(EditMessageText) == 0

    def test_filter(self):
        log = CallLog()
        log.record(send(1, "keep"))
        log.record(send(2, "drop"))

        found = log.filter(lambda call: call.chat_id == 1)

        assert [item.text for item in found] == ["keep"]

    def test_last_without_a_matching_call(self):
        log = CallLog()
        log.record(send(1, "a"))

        with pytest.raises(NoSuchCallError, match="No EditMessageText call"):
            log.last(EditMessageText)

    def test_first_without_any_call(self):
        with pytest.raises(NoSuchCallError, match="Recorded calls: none"):
            CallLog().first(SendMessage)

    def test_protocol_helpers(self):
        log = CallLog()

        assert not log
        assert len(log) == 0

        log.record(send(1, "a"))

        assert log
        assert len(log) == 1
        assert [type(item).__name__ for item in log] == ["SendMessage"]
        assert "SendMessage" in repr(log)

    def test_clear(self):
        log = CallLog()
        log.record(send(1, "a"))

        log.clear()

        assert log.count() == 0
