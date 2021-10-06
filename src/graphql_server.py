import json
import datetime
from decimal import Decimal
from typing import Iterable

import flask
from ariadne import graphql_sync, combine_multipart_data, make_executable_schema, load_schema_from_path, EnumType, \
    snake_case_fallback_resolvers, upload_scalar, ObjectType, ScalarType
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask

from src.api.base import BaseApi
from src.classes import Point
from src.enums import GRAPHQL_SCHEMA_ENUMS


def _get_scalars():
    point_scalar = ScalarType('Point')
    time_scalar = ScalarType('Time')
    date_scalar = ScalarType('Date')
    decimal_scalar = ScalarType('Decimal')

    # Point

    @point_scalar.serializer
    def serialize_point(value: Point):
        return ''.join(('(', str(value.x), ' ', str(value.y), ')')) if value is not None else None

    @point_scalar.value_parser
    def parse_point(value):
        return Point.from_string(value) if value is not None else None

    # Time

    @time_scalar.serializer
    def serialize_time(value):
        return value.hour * 3600 + value.minute * 60 if value is not None else None

    @time_scalar.value_parser
    def parse_time(value):
        return datetime.time(second=value) if value is not None else None

    # Date

    @date_scalar.serializer
    def serialize_date(value):
        return value.isoformat() if value is not None else None

    @date_scalar.value_parser
    def parse_date(value):
        return datetime.datetime.fromisoformat(value) if value else None

    # Decimal

    @decimal_scalar.serializer
    def serialize_decimal(value):
        return str(value) if value is not None else None

    @decimal_scalar.value_parser
    def parse_decimal(value):
        return Decimal(value) if value else None

    return upload_scalar, point_scalar, time_scalar, date_scalar, decimal_scalar


def setup_graphql_server(app: Flask, schema_path: str, api_list: Iterable[type], directive_dict):
    query = ObjectType('Query')
    mutation = ObjectType('Mutation')

    for api_class in api_list:
        api: BaseApi = api_class()
        for name, resolver in api.queries.items():
            query.set_field(name, resolver)
        for name, resolver in api.mutations.items():
            mutation.set_field(name, resolver)

    enum_types = [EnumType(x.__name__, x) for x in GRAPHQL_SCHEMA_ENUMS]

    type_defs = load_schema_from_path(schema_path)
    scalars = _get_scalars()

    schema = make_executable_schema(type_defs, query, mutation, snake_case_fallback_resolvers, *scalars, *enum_types,
                                    directives=directive_dict)

    @app.route('/graphql', methods=['GET'])
    def graphql_playground():
        return PLAYGROUND_HTML, 200

    @app.route('/graphql', methods=['POST'])
    def graphql_server():
        if flask.request.content_type.startswith('multipart/form-data'):
            data = combine_multipart_data(
                json.loads(flask.request.form.get("operations")),
                json.loads(flask.request.form.get("map")),
                dict(flask.request.files)
            )
        elif flask.request.is_json:
            data = flask.request.get_json()
        else:
            return '', 400

        success, result = graphql_sync(schema, data, context_value=flask.request, debug=app.debug)

        status_code = 200 if success else 400
        return flask.jsonify(result), status_code
