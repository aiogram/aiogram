import gc
import weakref

from aiogram.types import Chat, Message, Update


class TestUpdate:
    def test_event_type_keeps_no_reference_to_updates(self):
        references = []
        for update_id in range(1000):
            update = Update(
                update_id=update_id,
                message=Message(message_id=1, date=0, chat=Chat(id=1, type="private")),
            )
            assert update.event_type == "message"
            assert update.event is update.message
            references.append(weakref.ref(update))
        del update
        gc.collect()

        assert not [reference for reference in references if reference() is not None]

    def test_hash_is_update_id_based(self):
        assert hash(Update(update_id=1)) == hash(Update(update_id=1, pad="x"))
        assert {Update(update_id=1), Update(update_id=2)} == {
            Update(update_id=1),
            Update(update_id=2),
        }
