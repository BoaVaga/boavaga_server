from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class DbEngine:
    def __init__(self, conn_string, encoding='utf8'):
        self.engine = create_engine(conn_string, encoding=encoding)


class DbSessionMaker:
    def __init__(self, engine: DbEngine):
        self.session_maker = sessionmaker(bind=engine.engine)

    def __call__(self) -> Session:
        return self.session_maker()
