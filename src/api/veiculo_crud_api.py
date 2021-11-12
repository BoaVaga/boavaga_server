import logging
import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide

from src.api.base import BaseApi
from src.repo import VeiculoCrudRepo, RepoContainer

class VeiculoCrudApi(BaseApi):
    ERRO_DESCONHECIDO = 'erro_desconhecido'

    def __init__(self, veiculo_repo: VeiculoCrudRepo = Provide[RepoContainer.veiculo_crud_repo]):
        self.repo = veiculo_repo
        
        queries = {
            'getVeiculo': self.get_resolver,
            'listVeiculo': self.list_resolver
        }
        mutations = {}

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def get_resolver(self, _, _2, veiculo_id: str):
        sess = flask.g.session

        try:
            success, veiculo_or_error = self.repo.get(sess, veiculo_id)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on get_resolver', exc_info=ex)
            success, veiculo_or_error = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'veiculo': veiculo_or_error
            }
        else:
            return {
                'success': False,
                'error': veiculo_or_error
            }

    @convert_kwargs_to_snake_case
    def list_resolver(self, _, _2):
        sess = flask.g.session

        try:
            success, veiculos_or_error = self.repo.list(sess)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on list_resolver', exc_info=ex)
            success, veiculos_or_error = False, self.ERRO_DESCONHECIDO

        if success:
            return {
                'success': True,
                'veiculos': veiculos_or_error
            }
        else:
            return {
                'success': False,
                'error': veiculos_or_error
            }
    
