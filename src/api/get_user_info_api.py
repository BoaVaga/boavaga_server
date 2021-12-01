import flask
from ariadne import convert_kwargs_to_snake_case
from dependency_injector.wiring import Provide

from src.api.base import BaseApi
from src.container import Container
from src.enums import UserType
from src.services import Cached


class GetUserInfoApi(BaseApi):
    def __init__(self, cached: Cached = Provide[Container.cached]):
        self.cached = cached

        queries = {
            'getUser': self.get_user_resolver
        }
        mutations = {}

        super().__init__(queries, mutations)

    @convert_kwargs_to_snake_case
    def get_user_resolver(self, _, info):
        sess = flask.g.session
        user_sess = self.get_user_session(sess, self.cached, info)

        if user_sess is None:
            return {
                'logado': False
            }
        else:
            payload = {
                'logado': True,
                'tipo': user_sess.tipo
            }

            if user_sess.tipo == UserType.ESTACIONAMENTO:
                payload['admin_estacio'] = user_sess.user
            else:
                payload['admin_sistema'] = user_sess.user

            return payload
