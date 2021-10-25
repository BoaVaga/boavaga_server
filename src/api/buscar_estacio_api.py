import logging

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.classes import Point
from src.repo import BuscarEstacioRepo, RepoContainer


class BuscarEstacioApi(BaseApi):
    def __init__(self, buscar_repo: BuscarEstacioRepo = Provide[RepoContainer.buscar_estacio_repo]):
        self.repo = buscar_repo

        queries = {'buscarEstacio': self.buscar_estacio_resolver}
        mutations = {}

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def buscar_estacio_resolver(self, *_, coordenadas: Point):
        sess: Session = flask.g.session

        try:
            success, error_os_estacios = self.repo.buscar(sess, coordenadas)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on buscar_estacio_resolver', exc_info=ex)
            success, error_os_estacios = False, 'erro_desconhecido'

        if success:
            return {
                'success': True,
                'estacionamentos': error_os_estacios
            }
        else:
            return {
                'success': False,
                'error': error_os_estacios
            }
