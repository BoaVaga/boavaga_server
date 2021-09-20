from typing import Dict, Callable, Optional

import flask
from sqlalchemy.orm import Session

from src.classes import UserSession, SimpleUserSession
from src.services import Cached


class BaseApi:
    SESS_TOKEN_GROUP = 'sess_token'

    def __init__(self, queries: Dict[str, Callable], mutations: Dict[str, Callable]):
        self.queries = queries
        self.mutations = mutations

    def get_user_session(self, sess: Session, cached: Cached, info) -> Optional[UserSession]:
        request: flask.Request = info.context

        auth_header = request.headers.get('Authorization')
        if auth_header is not None and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            data: SimpleUserSession = cached.get(self.SESS_TOKEN_GROUP, token)

            if data is not None:
                user_sess = UserSession.from_simple_user_sess(data)
                user_sess.set_db_session(sess)
                return user_sess
