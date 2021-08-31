import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide, inject
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.container import Container
from src.models import AdminSistema
from src.services import Crypto, Cached


class AdminSistemaApi(BaseApi):
    EMAIL_JA_CADASTRADO = 'email_ja_cadastrado'

    @inject
    def __init__(self, crypto: Crypto = Provide[Container.crypto], cached: Cached = Provide[Container.cached]):
        self.crypto = crypto
        self.cached = cached

        queries = {}
        mutations = {
            'create_admin_sistema': self.create_admin_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def create_admin_resolver(self, *_, nome: str, email: str, senha: str):
        sess: Session = flask.g.session

        try:
            hash_senha = self.crypto.hash_password(senha.encode('utf8'))
            admin = AdminSistema(nome=nome, email=email, senha=hash_senha)
            sess.add(admin)
            sess.commit()

            payload = {
                'success': True,
                'admin_sistema': admin
            }
        except IntegrityError:
            sess.rollback()

            payload = {'success': False, 'error': self.EMAIL_JA_CADASTRADO}
        except Exception as ex:
            sess.rollback()

            payload = {'success': False, 'error': str(ex)}

        return payload
