import uuid

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.container import Container
from src.enums import UserType
from src.models import AdminSistema, UserSession, AdminEstacio
from src.services import Crypto, Cached


class AuthApi(BaseApi):
    SENHA_INCORRETA = 'senha_incorreta'
    EMAIL_NAO_ENCONTRADO = 'email_nao_encontrado'

    SESS_TOKEN_GROUP = 'sess_token'
    REVERSE_SESS_TOKEN_GROUP = 'rev_sess_token'

    def __init__(self, crypto: Crypto = Provide[Container.crypto], cached: Cached = Provide[Container.cached]):
        self.crypto = crypto
        self.cached = cached

        queries = {}
        mutations = {
            'login': self.login_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def login_resolver(self, *_, email: str, senha: str, tipo: str):
        sess: Session = flask.g.session

        try:
            tipo = UserType[tipo]

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

                    token = str(uuid.uuid4())
                    user_session = UserSession(tipo, admin.id)

                    self.cached.set(self.SESS_TOKEN_GROUP, token, user_session.to_simple_user_sess())
                    self.cached.set(self.REVERSE_SESS_TOKEN_GROUP, reverse_key, token)

                    payload = {
                        'success': True,
                        'token': token
                    }
                else:
                    payload = {'success': False, 'error': self.SENHA_INCORRETA}
            else:
                payload = {'success': False, 'error': self.EMAIL_NAO_ENCONTRADO}
        except Exception as ex:
            payload = {'success': False, 'error': str(ex)}

        return payload

    @staticmethod
    def _gen_reverse_session_key(tipo: UserType, user_id: int) -> str:
        return str(tipo.value) + ':' + str(user_id)
