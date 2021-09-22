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
from src.repo import PedidoCadastroRepo, RepoContainer
from src.services import Cached


class PedidoCadastroApi(BaseApi):
    def __init__(self, pedido_cad_repo: PedidoCadastroRepo = Provide[RepoContainer.pedido_cadastro_repo],
                 cached: Cached = Provide[Container.cached]):
        self.pedido_cad_repo = pedido_cad_repo
        self.cached = cached

        queries = {}
        mutations = {
            'createPedidoCadastro': self.create_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def create_resolver(self, _, info, nome: str, telefone: str, endereco: dict, foto: FileStorage):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        end = Endereco(logradouro=endereco['logradouro'], estado=endereco['estado'], cep=endereco['cep'],
                       cidade=endereco['cidade'], bairro=endereco['bairro'], numero=endereco['numero'])

        fstream = FlaskFileStream(foto)
        success, error_or_pedido = self.pedido_cad_repo.create(user_sess, sess, nome, telefone, end, fstream)

        if success:
            return {
                'success': True,
                'pedidoCadastro': error_or_pedido
            }
        else:
            return {
                'success': False,
                'error': error_or_pedido
            }
