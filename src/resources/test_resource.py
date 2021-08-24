from dependency_injector.wiring import inject, Provide
from sqlalchemy.orm import Session
from flask_restful import Resource
import flask

from src.container import Container
from src.models import Endereco
from src.services import DbSessionMaker


class TestResource(Resource):
    @inject
    def __init__(self, name: str = Provide[Container.config.test.test_abc],
                 db_session_maker: DbSessionMaker = Provide[Container.db_session_maker]):
        self.name = name
        self.db_session_maker = db_session_maker

    def get(self):
        session: Session = flask.g.session

        ret = session.query(Endereco.cidade).all()
        return 'Vazio' if len(ret) == 0 else f'Cidade: {ret[0].cidade}'
