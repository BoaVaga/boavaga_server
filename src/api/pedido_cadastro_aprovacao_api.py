import logging

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.classes import Point
from src.container import Container
from src.repo import PedidoCadastroAprovacaoRepo, RepoContainer
from src.services import Cached


class PedidoCadastroAprovacaoApi(BaseApi):
    def __init__(self, repo: PedidoCadastroAprovacaoRepo = Provide[RepoContainer.pedido_cadastro_aprovacao_repo],
                 cached: Cached = Provide[Container.cached]):
        self.repo = repo
        self.cached = cached

        queries = {}
        mutations = {
            'acceptPedidoCadastro': self.accept_resolver,
            'rejectPedidoCadastro': self.reject_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def accept_resolver(self, _, info, pedido_id: str, coordenadas: Point):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            ok, estacio_or_error = self.repo.accept(user_sess, sess, pedido_id, coordenadas)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on accept_resolver', exc_info=ex)
            ok, estacio_or_error = False, 'erro_desconhecido'

        if ok:
            return {
                'success': True,
                'estacionamento': estacio_or_error
            }
        else:
            return {
                'success': False,
                'error': estacio_or_error
            }

    @convert_kwargs_to_snake_case
    def reject_resolver(self, _, info, pedido_id: str, motivo: str):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error = self.repo.reject(user_sess, sess, pedido_id, motivo)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on reject_resolver', exc_info=ex)
            success, error = False, 'erro_desconhecido'

        return {
            'success': success,
            'error': error
        }
