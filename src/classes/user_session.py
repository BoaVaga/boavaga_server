from typing import Optional

from src.enums import UserType
from src.models import AdminSistema, AdminEstacio
from src.classes.i_user import IUser


class SimpleUserSession:
    def __init__(self, tipo: int, user_id: int):
        self.tipo: int = tipo
        self.user_id: int = user_id


class UserSession:
    def __init__(self, tipo: UserType, user_id: int):
        self.tipo: UserType = tipo
        self.user_id: int = user_id

        self._user: Optional[IUser] = None
        self._sess = None

    @property
    def user(self) -> Optional[IUser]:
        if self._user is None:
            if self._sess is None:
                raise RuntimeError('The database session was not set, so it is not possible to load the user. '
                                   'Remember to call set_db_session.')

            if self.tipo == UserType.SISTEMA:
                return self._sess.query(AdminSistema).get(self.user_id)
            else:
                return self._sess.query(AdminEstacio).get(self.user_id)

        return self._user

    @user.setter
    def user(self, value: IUser):
        self._user = value

    @staticmethod
    def from_simple_user_sess(simple_user_sess: SimpleUserSession):
        return UserSession(UserType(simple_user_sess.tipo), simple_user_sess.user_id)

    def to_simple_user_sess(self) -> SimpleUserSession:
        return SimpleUserSession(self.tipo.value, self.user_id)

    def set_db_session(self, sess):
        self._sess = sess

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, UserSession):
            return NotImplemented

        return self.user_id == other.user_id and self.tipo == other.tipo
