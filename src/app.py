import pathlib

import flask
from flask import Flask
from flask_cors import CORS

from src.api import APIS
from src.container import Container
from src.graphql_server import setup_graphql_server
from src.repo import RepoContainer
from src.services import DbSessionMaker


def create_app(container: Container, repo_container: RepoContainer):
    app = Flask(__name__)
    app.container = container
    app.repo_container = repo_container

    graphql_schema_path = pathlib.Path(__file__).parent / 'schema.graphql'
    setup_graphql_server(app, str(graphql_schema_path), APIS, {})

    setup_db_connection(app, container.db_session_maker())

    CORS(app, origins='*')

    return app


def setup_db_connection(app: Flask, session_maker: DbSessionMaker):
    @app.before_request
    def create_session():
        flask.g.session = session_maker()

    @app.teardown_appcontext
    def shutdown_session(response_or_exc):
        flask.g.session.rollback()
        flask.g.session.close()
