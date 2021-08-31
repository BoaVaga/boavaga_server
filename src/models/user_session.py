from src.enums import UserType


class SimpleUserSession:
    def __init__(self, tipo: int, user_id: int):
        self.tipo: int = tipo
        self.user_id: int = user_id


class UserSession:
    def __init__(self, tipo: UserType, user_id: int):
        self.tipo: UserType = tipo
        self.user_id: int = user_id

    @staticmethod
    def from_simple_user_sess(simple_user_sess: SimpleUserSession):
        return UserSession(UserType(simple_user_sess.tipo), simple_user_sess.user_id)

    def to_simple_user_sess(self) -> SimpleUserSession:
        return SimpleUserSession(self.tipo.value, self.user_id)
