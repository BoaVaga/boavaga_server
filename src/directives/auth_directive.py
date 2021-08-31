import flask
from ariadne import SchemaDirectiveVisitor
from dependency_injector.wiring import Provide, inject
from graphql import default_field_resolver

from src.container import Container
from src.enums import UserType
from src.models import SimpleUserSession
from src.services import Cached


class AuthDirective(SchemaDirectiveVisitor):
    SESS_TOKEN_GROUP = 'sess_token'

    @inject
    def __init__(self, *args, cached: Cached = Provide[Container.cached], **kwargs):
        self.cached = cached

        super().__init__(*args, **kwargs)

    def visit_field_definition(self, field, object_type):
        required = UserType[self.args.get('requires')]
        original_resolver = field.resolve or default_field_resolver

        def resolver(obj, info, **kwargs):
            request: flask.Request = info.context

            auth_header = request.headers.get('Authorization')
            if auth_header is not None and auth_header.startswith('Bearer '):
                token = auth_header[7:]
                data: SimpleUserSession = self.cached.get(self.SESS_TOKEN_GROUP, token)
                if data is not None and data.tipo <= required.value:
                    return original_resolver(obj, info, **kwargs)

            raise Exception('Você não tem permissão necessária')

        field.resolve = resolver
        return field
