import pathlib
from typing import Iterable

import flask
from ariadne import graphql_sync, load_schema_from_path, make_executable_schema, snake_case_fallback_resolvers, \
    ObjectType
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask
from flask_cors import CORS

from src.api import APIS
from src.api.base import BaseApi
from src.container import create_container
from src.directives import DIRECTIVES
from src.services import DbSessionMaker


def create_app(config_filepath: str):
    container = create_container(config_filepath)

    app = Flask(__name__)
    app.container = container

    graphql_schema_path = pathlib.Path(__file__).parent / 'schema.graphql'
    setup_graphql_server(app, str(graphql_schema_path), APIS, DIRECTIVES)

    setup_db_connection(app, container.db_session_maker())

    CORS(app, origins='*')

    return app


def setup_db_connection(app: Flask, session_maker: DbSessionMaker):
    @app.before_request
    def create_session():
        flask.g.session = session_maker()

    @app.teardown_appcontext
    def shutdown_session(response_or_exc):
        flask.g.session.commit()
        flask.g.session.close()


def setup_graphql_server(app: Flask, schema_path: str, api_list: Iterable[type], directive_dict):
    query = ObjectType('Query')
    mutation = ObjectType('Mutation')

    for api_class in api_list:
        api: BaseApi = api_class()
        for name, resolver in api.queries.items():
            query.set_field(name, resolver)
        for name, resolver in api.mutations.items():
            mutation.set_field(name, resolver)

    type_defs = load_schema_from_path(schema_path)
    schema = make_executable_schema(type_defs, query, mutation, snake_case_fallback_resolvers,
                                    directives=directive_dict)

    @app.route('/graphql', methods=['GET'])
    def graphql_playground():
        return PLAYGROUND_HTML, 200

    @app.route('/graphql', methods=['POST'])
    def graphql_server():
        if flask.request.is_json:
            data = flask.request.get_json()
            success, result = graphql_sync(schema, data, context_value=flask.request, debug=app.debug)

            status_code = 200 if success else 400
            return flask.jsonify(result), status_code
        else:
            return '', 400
