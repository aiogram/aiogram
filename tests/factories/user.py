import factory

from aiogram.api.types import User
from tests.factories import sequences


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = sequences.id_
    first_name = factory.Sequence(lambda n: f"First name #{n}")
    is_bot = False

    def __new__(cls, *args, **kwargs) -> "UserFactory.Meta.model":
        """
        This is a dirty hack for correct type hints
        See https://github.com/FactoryBoy/factory_boy/issues/468#issuecomment-505646794
        """
        return super().__new__(*args, **kwargs)
