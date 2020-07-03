import factory

from aiogram.api.types import User
from tests.factories import sequences


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = sequences.id_
    first_name = factory.Sequence(lambda n: f"First name #{n}")
    is_bot = False
