from typing import Tuple

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session


def make_engine(conn_string: str):
    return create_engine(conn_string)


def make_general_db_setup(engine) -> Tuple[object, object, Session]:
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn)

    return conn, trans, session


def general_db_teardown(conn, trans, session):
    session.close()
    trans.rollback()
    conn.close()


def make_savepoint(conn, sess):
    nested = conn.begin_nested()

    @event.listens_for(sess, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested

        if not nested.is_active:
            nested = conn.begin_nested()

    return nested
