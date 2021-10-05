import logging

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

from src.api.base import BaseApi
from src.classes import FlaskFileStream
from src.container import Container
from src.enums import EstadosEnum
from src.models import Endereco
from src.repo import PedidoCadastroCrudRepo, RepoContainer
from src.services import Cached


class PedidoCadastroApi(BaseApi):
    ERRO_DESCONHECIDO = 'erro_desconhecido'

    def __init__(self, pedido_cad_crud_repo: PedidoCadastroCrudRepo = Provide[RepoContainer.pedido_cadastro_crud_repo],
                 cached: Cached = Provide[Container.cached]):
        self.pedido_cad_crud_repo = pedido_cad_crud_repo
        self.cached = cached

        queries = {
            'listPedidoCadastro': self.list_resolver,
            'getPedidoCadastro': self.get_resolver
        }
        mutations = {
            'createPedidoCadastro': self.create_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def create_resolver(self, _, info, nome: str, telefone: str, endereco: dict, foto: FileStorage):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        endereco = {k: v.strip() if isinstance(v, str) else v for k, v in endereco.items()}

        end = Endereco.from_dict(endereco)
        val_res = end.validate()

        if val_res is not None:
            return {
                'success': False,
                'error': val_res
            }

        try:
            fstream = FlaskFileStream(foto)
            success, error_or_pedido = self.pedido_cad_crud_repo.create(user_sess, sess, nome, telefone, end, fstream)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on create_resolver', exc_info=ex)
            success, error_or_pedido = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'pedido_cadastro': error_or_pedido
            }
        else:
            return {
                'success': False,
                'error': error_or_pedido
            }

    @convert_kwargs_to_snake_case
    def list_resolver(self, _, info, amount: int = 0, index: int = 0):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error_or_pedidos = self.pedido_cad_crud_repo.list(user_sess, sess, amount=amount, index=index)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on list_resolver', exc_info=ex)
            success, error_or_pedidos = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'pedidos_cadastro': error_or_pedidos
            }
        else:
            return {
                'success': False,
                'error': error_or_pedidos
            }

    @convert_kwargs_to_snake_case
    def get_resolver(self, _, info, pedido_id: str):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error_or_pedido = self.pedido_cad_crud_repo.get(user_sess, sess, pedido_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on get_resolver', exc_info=ex)
            success, error_or_pedido = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'pedido_cadastro': error_or_pedido
            }
        else:
            return {
                'success': False,
                'error': error_or_pedido
            }
