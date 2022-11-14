import typing

from aiogram.dispatcher.storage import BaseStorage
from sqlalchemy import Column, Integer, String, ForeignKey
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()


class State(SqlAlchemyBase):
    """
    State object linked to 'states' table of DB
    """
    __tablename__ = "states"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    chat = Column(Integer, index=True)
    user = Column(Integer, index=True)
    state = Column(String)

    data = orm.relationship("StateData", back_populates="state")


class StateData(SqlAlchemyBase):
    """
    Data object linked to 'state_data' table of DB
    """
    __tablename__ = "state_data"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    chat_user_pair = Column(Integer, ForeignKey("states.id"))
    key = Column(String)
    value = Column(String)

    state = orm.relationship("State", back_populates="data")


class SQLiteStorage(BaseStorage):
    """
    SQLite based states storage.
    """

    def __init__(
            self,
            url: str = None,
            path: str = None
    ):
        if not url:
            if not path or not path.strip():
                raise Exception("DB file is not specified")
            url = f'sqlite:///{path.strip()}?check_same_thread=False'

        self.__factory = None

        engine = sa.create_engine(url, echo=False)
        self.__factory = orm.sessionmaker(bind=engine)
        SqlAlchemyBase.metadata.create_all(engine)

    def create_session(self) -> Session:
        return self.__factory()

    async def close(self):
        """
        You have to override this method and use when application shutdowns.
        Perhaps you would like to save data and etc.
        :return:
        """
        raise NotImplementedError

    async def wait_closed(self):
        """
        You have to override this method for all asynchronous storages (e.g., Redis).
        :return:
        """
        raise NotImplementedError

    @classmethod
    def check_address(cls, *,
                      chat: typing.Union[str, int, None] = None,
                      user: typing.Union[str, int, None] = None,
                      ) -> (typing.Union[str, int], typing.Union[str, int]):
        """
        In all storage's methods chat or user is always required.
        If one of them is not provided, you have to set missing value based on the provided one.
        This method performs the check described above.
        :param chat: chat_id
        :param user: user_id
        :return:
        """
        if chat is None and user is None:
            raise ValueError('`user` or `chat` parameter is required but no one is provided!')

        if user is None:
            user = chat

        elif chat is None:
            chat = user

        return chat, user

    async def query_state(self,
                          chat: typing.Union[str, int],
                          user: typing.Union[str, int],
                          session=None):
        if not session:
            session = self.create_session()

        state = session.query(State).filter(State.chat == chat, State.user == user).first()
        return state

    async def get_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        """
        Get current state of user in chat. Return `default` if no record is found.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :param default:
        :return:
        """
        chat, user = self.check_address(chat=chat, user=user)
        session = self.create_session()
        state = await self.query_state(chat, user, session=session)

        if state:
            return state.state
        return default

    async def get_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       default: typing.Optional[typing.Dict] = None) -> typing.Dict:
        """
        Get state-data for user in chat. Return `default` if no data is provided in storage.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :param default:
        :return:
        """
        chat, user = self.check_address(chat=chat, user=user)
        session = self.create_session()
        state = await self.query_state(chat, user, session=session)
        if state:
            data_list = state.data
            return {i.key: i.value for i in data_list}
        return default

    async def set_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        """
        Set new state for user in chat
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :param state:
        """
        chat, user = self.check_address(chat=chat, user=user)
        session = self.create_session()
        qstate = await self.query_state(chat, user, session=session)
        if not qstate:
            qstate = State(chat=chat, user=user)
            session.add(qstate)
            session.commit()

        qstate.state = state
        session.commit()

    async def set_data(self, *,
                       chat: typing.Union[str, int, None] = None,
                       user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        """
        Set data for user in chat
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :param data:
        """
        chat, user = self.check_address(chat=chat, user=user)
        await self.reset_data(chat=chat, user=user)
        session = self.create_session()
        state = await self.query_state(chat, user, session=session)
        if not state:
            state = State(chat=chat, user=user)
            session.add(state)
            session.commit()

        for k in data.keys():
            state_data = session.query(StateData).filter(
                StateData.state == state,
                StateData.key == k
            ).first()

            if not state_data:
                state = await self.query_state(chat, user, session=session)
                state.data.append(StateData(key=k, value=data[k]))
            else:
                state_data.value = data[k]
            session.commit()

    async def update_data(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None,
                          **kwargs):
        """
        Update data for user in chat
        You can use data parameter or|and kwargs.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param data:
        :param chat:
        :param user:
        :param kwargs:
        :return:
        """
        if not data:
            data = kwargs
        await self.set_data(chat=chat, user=user, data=data)

    async def reset_data(self, *,
                         chat: typing.Union[str, int, None] = None,
                         user: typing.Union[str, int, None] = None):
        """
        Reset data for user in chat.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :return:
        """
        chat, user = self.check_address(chat=chat, user=user)
        session = self.create_session()
        state = await self.query_state(chat, user, session=session)
        if not state:
            state = State(chat=chat, user=user)
            session.add(state)
            session.commit()

        for i in state.data:
            session.delete(i)
        session.commit()

    async def reset_state(self, *,
                          chat: typing.Union[str, int, None] = None,
                          user: typing.Union[str, int, None] = None,
                          with_data: typing.Optional[bool] = True):
        """
        Reset state for user in chat.
        You may desire to use this method when finishing conversations.
        Chat or user is always required. If one of this is not presented,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :param with_data:
        :return:
        """
        chat, user = self.check_address(chat=chat, user=user)
        await self.set_state(chat=chat, user=user, state=None)
        if with_data:
            await self.set_data(chat=chat, user=user, data={})

    async def finish(self, *,
                     chat: typing.Union[str, int, None] = None,
                     user: typing.Union[str, int, None] = None):
        """
        Finish conversation for user in chat.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :return:
        """
        await self.reset_state(chat=chat, user=user, with_data=True)

    def has_bucket(self):
        return False

    async def get_bucket(self, *,
                         chat: typing.Union[str, int, None] = None,
                         user: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        """
        Get bucket for user in chat. Return `default` if no data is provided in storage.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :param default:
        :return:
        """
        raise NotImplementedError

    async def set_bucket(self, *,
                         chat: typing.Union[str, int, None] = None,
                         user: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        """
        Set bucket for user in chat
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :param bucket:
        """
        raise NotImplementedError

    async def update_bucket(self, *,
                            chat: typing.Union[str, int, None] = None,
                            user: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None,
                            **kwargs):
        """
        Update bucket for user in chat
        You can use bucket parameter or|and kwargs.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param bucket:
        :param chat:
        :param user:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    async def reset_bucket(self, *,
                           chat: typing.Union[str, int, None] = None,
                           user: typing.Union[str, int, None] = None):
        """
        Reset bucket dor user in chat.
        Chat or user is always required. If one of them is not provided,
        you have to set missing value based on the provided one.
        :param chat:
        :param user:
        :return:
        """
        await self.set_bucket(chat=chat, user=user, bucket={})

    @staticmethod
    def resolve_state(value):
        from aiogram.dispatcher.filters.state import State

        if value is None:
            return

        if isinstance(value, str):
            return value

        if isinstance(value, State):
            return value.state

        return str(value)
