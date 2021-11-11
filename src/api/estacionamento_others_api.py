import logging
import datetime
from typing import Optional
from decimal import Decimal

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.container import Container
from src.repo import EstacionamentoOthersRepo, RepoContainer
from src.services import Cached


class EstacionamentoOthersApi(BaseApi):
    ERRO_DESCONHECIDO = 'erro_desconhecido'

    def __init__(self, repo: EstacionamentoOthersRepo = Provide[RepoContainer.estacionamento_others_repo],
                 cached: Cached = Provide[Container.cached]):
        self.cached = cached
        self.repo = repo

        queries = {}
        mutations = {
            'atualizarQtdVagaLivre': self.atualizar_qtd_vaga_livre_resolver,
            'editEstacioHorarioPadrao': self.edit_horario_padrao_resolver,
            'editEstacioValorHora': self.edit_valor_hora_resolver,
            'deleteEstacioValorHora': self.delete_valor_hora_resolver,
            'deleteEstacioHorarioPadrao': self.delete_horario_padrao_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def atualizar_qtd_vaga_livre_resolver(self, _, info, num_vaga: int):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error = self.repo.atualizar_vagas_livres(user_sess, sess, num_vaga)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on atualizar_qtd_vaga_livre_resolver', exc_info=ex)
            success, error = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True
            }
        else:
            return {
                'success': False,
                'error': error
            }

    @convert_kwargs_to_snake_case
    def edit_horario_padrao_resolver(self, _, info, dia: str, hora_abre: datetime.time, hora_fecha: datetime.time,
                                     estacio_id: Optional[str] = None):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error_or_hora = self.repo.edit_horario_padrao(user_sess, sess, dia, hora_abre, hora_fecha, estacio_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on edit_horario_padrao_resolver', exc_info=ex)
            success, error_or_hora = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'horario_padrao': error_or_hora
            }
        else:
            return {
                'success': False,
                'error': error_or_hora
            }

    @convert_kwargs_to_snake_case
    def edit_valor_hora_resolver(self, _, info, veiculo_id: str, valor: Decimal, estacio_id: Optional[str] = None):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error_or_valor = self.repo.edit_valor_hora(user_sess, sess, veiculo_id, valor, estacio_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on edit_valor_hora_resolver', exc_info=ex)
            success, error_or_valor = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'valor_hora': error_or_valor
            }
        else:
            return {
                'success': False,
                'error': error_or_valor
            }

    @convert_kwargs_to_snake_case
    def delete_horario_padrao_resolver(self, _, info, dia: str, estacio_id: Optional[str] = None):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error = self.repo.edit_horario_padrao(user_sess, sess, dia, None, None, estacio_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on delete_horario_padrao_resolver', exc_info=ex)
            success, error = False, self.ERRO_DESCONHECIDO

        if success:
            return {'success': True}
        else:
            return {'success': False, 'error': error}

    @convert_kwargs_to_snake_case
    def delete_valor_hora_resolver(self, _, info, veiculo_id: str, estacio_id: Optional[str] = None):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error = self.repo.delete_valor_hora(user_sess, sess, veiculo_id, estacio_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on delete_valor_hora_resolver', exc_info=ex)
            success, error = False, self.ERRO_DESCONHECIDO

        if success:
            return {'success': True}
        else:
            return {'success': False, 'error': error}
