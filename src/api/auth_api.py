import logging

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.enums import UserType
from src.repo import AuthRepo, RepoContainer


class AuthApi(BaseApi):
    ERRO_DESCONHECIDO = 'erro_desconhecido'

    def __init__(self, auth_repo: AuthRepo = Provide[RepoContainer.auth_repo]):
        self.auth_repo = auth_repo

        queries = {}
        mutations = {
            'login': self.login_resolver,
            'enviarEmailSenha': self.enviar_email_senha_resolver,
            'recuperarSenha': self.recuperar_senha_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def login_resolver(self, *_, email: str, senha: str, tipo: UserType):
        sess: Session = flask.g.session

        try:
            success, error_or_token = self.auth_repo.login(sess, email, senha, tipo)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on login_resolver', exc_info=ex)
            success, error_or_token = False, self.ERRO_DESCONHECIDO

        if success:
            payload = {
                'success': True,
                'token': error_or_token
            }
        else:
            payload = {
                'success': False,
                'error': error_or_token
            }

        return payload

    @convert_kwargs_to_snake_case
    def enviar_email_senha_resolver(self, *_, email: str, tipo: UserType):
        sess = flask.g.session

        try:
            success, error = self.auth_repo.enviar_email_senha(sess, email, tipo)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on enviar_email_senha_resolver', exc_info=ex)
            success, error = False, self.ERRO_DESCONHECIDO

        return {
            'success': success,
            'error': error
        }

    @convert_kwargs_to_snake_case
    def recuperar_senha_resolver(self, *_, code: str, nova_senha: str):
        sess = flask.g.session

        try:
            success, error = self.auth_repo.recuperar_senha(sess, nova_senha, code)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on recuperar_senha_resolver', exc_info=ex)
            success, error = False, self.ERRO_DESCONHECIDO

        return {
            'success': success,
            'error': error
        }


    @staticmethod
    def _gen_reverse_session_key(tipo: UserType, user_id: int) -> str:
        return str(tipo.value) + ':' + str(user_id)
