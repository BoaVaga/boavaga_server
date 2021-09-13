from typing import Tuple

from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.container import Container
from src.enums import UserType
from src.models import AdminSistema, AdminEstacio, UserSession
from src.services import Crypto, Cached


class AuthRepo:
    SENHA_INCORRETA = 'senha_incorreta'
    EMAIL_NAO_ENCONTRADO = 'email_nao_encontrado'

    SESS_TOKEN_GROUP = 'sess_token'
    REVERSE_SESS_TOKEN_GROUP = 'rev_sess_token'

    @inject
    def __init__(self, crypto: Crypto = Provide[Container.crypto], cached: Cached = Provide[Container.cached]):
        self.crypto = crypto
        self.cached = cached

    def login(self, sess: Session, email: str, senha: str, tipo: UserType) -> Tuple[bool, str]:
        try:
            if tipo == UserType.SISTEMA:
                admin = sess.query(
                    AdminSistema.id, AdminSistema.senha
                ).filter(AdminSistema.email == email).first()
            else:
                admin = sess.query(
                    AdminEstacio.id, AdminEstacio.senha
                ).filter(AdminEstacio.email == email).first()

            if admin is not None:
                if self.crypto.check_password(senha.encode('utf8'), admin.senha):
                    reverse_key = self._gen_reverse_session_key(tipo, admin.id)
                    old_token = self.cached.get(self.REVERSE_SESS_TOKEN_GROUP, reverse_key)

                    if old_token is not None:
                        self.cached.remove(self.SESS_TOKEN_GROUP, old_token)

                    user_session = UserSession(tipo, admin.id)
                    token = self._gen_token(old_token)

                    self.cached.set(self.SESS_TOKEN_GROUP, token, user_session.to_simple_user_sess())
                    self.cached.set(self.REVERSE_SESS_TOKEN_GROUP, reverse_key, token)

                    return True, token
                else:
                    return False, self.SENHA_INCORRETA
            else:
                return False, self.EMAIL_NAO_ENCONTRADO
        except Exception as ex:
            return False, str(ex)

    @staticmethod
    def _gen_reverse_session_key(tipo: UserType, user_id: int) -> str:
        return str(tipo.value) + ':' + str(user_id)

    def _gen_token(self, old_token: str) -> str:
        token = None
        while token is None or self.cached.contains(self.SESS_TOKEN_GROUP, token) or token == old_token:
            token = self.crypto.random_hex_string(16)

        return token
