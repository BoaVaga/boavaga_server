import logging
from typing import Optional, Iterable

import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide
from sqlalchemy.orm import Session

from src.api.base import BaseApi
from src.classes import ValorHoraInput
from src.container import Container
from src.models import HorarioPadrao
from src.repo import EstacionamentoCrudRepo, RepoContainer
from src.services import Cached


class EstacionamentoCrudApi(BaseApi):
    ERRO_DESCONHECIDO = 'erro_desconhecido'

    def __init__(self, estacio_crud_repo: EstacionamentoCrudRepo = Provide[RepoContainer.estacionamento_crud_repo],
                 cached: Cached = Provide[Container.cached]):
        self.cached = cached
        self.repo = estacio_crud_repo

        queries = {}
        mutations = {'finishEstacionamentoCadastro': self.finish_estacionamento_cadastro_resolver}

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
