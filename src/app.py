import flask
from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from src.resources import resources
from src.container import create_container
from src.services import DbSessionMaker


def create_app(config_filepath: str):
    container = create_container(config_filepath)

    app = Flask(__name__)
    app.container = container

    api = Api(app)
    for resource in resources:
        api.add_resource(*resource)

    setup_db_connection(app, container.db_session_maker())

    CORS(app, origins=app.config.get('CORS_ORIGIN'))

    return app


def setup_db_connection(app: Flask, session_maker: DbSessionMaker):
    @app.before_request
    def create_session():
        flask.g.session = session_maker()

    @app.teardown_appcontext
    def shutdown_session(response_or_exc):
        flask.g.session.commit()
        flask.g.session.close()
