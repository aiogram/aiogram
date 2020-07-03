import factory

from aiogram.api.types import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n)
    first_name = factory.Sequence(lambda n: f"First name #{n}")
    last_name = factory.Sequence(lambda n: f"Last name #{n}")
    is_bot = False
