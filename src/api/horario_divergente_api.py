import logging
import flask
import datetime
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.services import Cached
from src.container import Container
from src.repo import HorarioDivergenteRepo, RepoContainer
from src.api.base import BaseApi


class HorarioDivergenteApi(BaseApi):
    ERRO_DESCONHECIDO = 'erro_desconhecido'

    def __init__(self, repo: HorarioDivergenteRepo = Provide[RepoContainer.horario_divergente_repo],
                 cached: Cached = Provide[Container.cached]):
        self.repo = repo
        self.cached = cached

        queries = {}
        mutations = {
            'setHorarioDivergente': self.set_resolver,
            'deleteHorarioDivergente': self.delete_resolver
        }

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def set_resolver(self, _, info, data: datetime.date, hora_abre: datetime.time, hora_fecha: datetime.time):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, horad_or_error = self.repo.set(user_sess, sess, data, hora_abre, hora_fecha)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on set_resolver()', exc_info=ex)
            success, horad_or_error = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'horario_divergente': horad_or_error
            }
        else:
            return {
                'success': False,
                'error': horad_or_error
            }

    @convert_kwargs_to_snake_case
    def delete_resolver(self, _, info, data: datetime.date):
        sess: Session = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        try:
            success, error = self.repo.delete(user_sess, sess, data)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on set_resolver()', exc_info=ex)
            success, error = False, self.ERRO_DESCONHECIDO

        return {
            'success': success,
            'error': error
        }
