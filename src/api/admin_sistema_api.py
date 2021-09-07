import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.repo import AdminSistemaRepo, RepoContainer


class AdminSistemaApi(BaseApi):
    @inject
    def __init__(self, admin_sistema_repo: AdminSistemaRepo = Provide[RepoContainer.admin_sistema_repo]):
        self.repo = admin_sistema_repo

        queries = {}
        mutations = {
            'createAdminSistema': self.create_admin_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def create_admin_resolver(self, *_, nome: str, email: str, senha: str):
        sess: Session = flask.g.session

        success, error_or_admin = self.repo.create_admin(sess, nome, email, senha)
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
