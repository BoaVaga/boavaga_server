import logging

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
        mutations = {'atualizarQtdVagaLivre': self.atualizar_qtd_vaga_livre_resolver}

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
