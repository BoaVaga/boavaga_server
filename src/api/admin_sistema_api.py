import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.container import Container
from src.repo import AdminSistemaRepo, RepoContainer
from src.services import Cached


class AdminSistemaApi(BaseApi):
    @inject
    def __init__(self, admin_sistema_repo: AdminSistemaRepo = Provide[RepoContainer.admin_sistema_repo],
                 cached: Cached = Provide[Container.cached]):
        self.repo = admin_sistema_repo
        self.cached = cached

        queries = {}
        mutations = {
            'createAdminSistema': self.create_admin_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def create_admin_resolver(self, _, info, nome: str, email: str, senha: str):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        success, error_or_admin = self.repo.create_admin(user_sess, sess, nome, email, senha)
        if success:
            payload = {
                'success': True,
                'adminSistema': error_or_admin
            }
        else:
            payload = {
                'success': False,
                'error': error_or_admin
            }

        return payload
