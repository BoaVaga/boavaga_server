import logging
from typing import Optional, Iterable

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.classes import ValorHoraInput, FileStream, FlaskFileStream
from src.container import Container
from src.models import HorarioPadrao, Endereco
from src.repo import EstacionamentoCrudRepo, RepoContainer
from src.services import Cached


class EstacionamentoCrudApi(BaseApi):
    ERRO_DESCONHECIDO = 'erro_desconhecido'

    def __init__(self, estacio_crud_repo: EstacionamentoCrudRepo = Provide[RepoContainer.estacionamento_crud_repo],
                 cached: Cached = Provide[Container.cached]):
        self.cached = cached
        self.repo = estacio_crud_repo

        queries = {
            'listEstacionamento': self.list_estacio_resolver,
            'getEstacionamento': self.get_estacio_resolver
        }
        mutations = {
            'finishEstacionamentoCadastro': self.finish_estacionamento_cadastro_resolver,
            'editEstacionamento': self.edit_estacionamento_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def finish_estacionamento_cadastro_resolver(
        self, _, info,
        total_vaga: int,
        horario_padrao: dict,
        valores_hora: Optional[Iterable[dict]] = None,
        estacio_id: Optional[str] = None,
        descricao: Optional[str] = None
    ):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        horario_padrao_real = HorarioPadrao.from_dict(horario_padrao)
        valores_hora_real = [ValorHoraInput.from_dict(d) for d in valores_hora] if valores_hora else None

        try:
            success, error_or_estacio = self.repo.create(user_sess, sess, total_vaga, horario_padrao_real,
                                                         valores_hora_real, estacio_id, descricao)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on finish_estacionamento_cadastro_resolver', exc_info=ex)
            success, error_or_estacio = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'estacionamento': error_or_estacio
            }
        else:
            return {
                'success': False,
                'error': error_or_estacio
            }

    def edit_estacionamento_resolver(
        self, _, info, 
        nome: Optional[str] = None,
        telefone: Optional[str] = None,
        endereco: Optional[Endereco] = None,
        total_vaga: Optional[int] = None,
        descricao: Optional[str] = None,
        foto: Optional[FileStream] = None,
        estacio_id: Optional[str] = None
    ):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        end = fstream = None

        if endereco:
            endereco = {k: v.strip() if isinstance(v, str) else v for k, v in endereco.items()}

            end = Endereco.from_dict(endereco)
            val_res = end.validate()

            if val_res is not None:
                return {'success': False, 'error': val_res}

        try:
            if foto:
                fstream = FlaskFileStream(foto)

            success, error_or_estacio = self.repo.edit(user_sess, sess, nome=nome, telefone=telefone, endereco=end, total_vaga=total_vaga,
                                                       descricao=descricao, foto=fstream, estacio_id=estacio_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on edit_estacionamento_resolver', exc_info=ex)
            success, error_or_estacio = False, self.ERRO_DESCONHECIDO

        if success:
            return {'success': True, 'estacionamento': error_or_estacio}
        else:
            return {'success': False, 'error': error_or_estacio}

    @convert_kwargs_to_snake_case
    def list_estacio_resolver(self, _, info, amount: int = 0, index: int = 0):
        sess = flask.g.session

        try:
            success, estacios_or_error = self.repo.list(sess, amount, index)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on list_estacio_resolver', exc_info=ex)
            success, estacios_or_error = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'estacionamentos': estacios_or_error
            }
        else:
            return {
                'success': False,
                'error': estacios_or_error
            }

    @convert_kwargs_to_snake_case
    def get_estacio_resolver(self, _, info, estacio_id: Optional[str] = None):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, estacio_or_error = self.repo.get(user_sess, sess, estacio_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on get_estacio_resolver', exc_info=ex)
            success, estacio_or_error = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'estacionamento': estacio_or_error
            }
        else:
            return {
                'success': False,
                'error': estacio_or_error
            }
