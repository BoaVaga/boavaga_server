from sgqlc.types import String, Type, Boolean, ID, Field, Enum


class AdminSistemaNode(Type):
    id = ID
    nome = String
    email = String


class CreateResNode(Type):
    success = Boolean
    error = String
    admin_sistema = AdminSistemaNode


class UserTypeNode(Enum):
    __choices__ = ('SISTEMA', 'ESTACIONAMENTO')


class LoginResNode(Type):
    success = Boolean
    error = String
    token = String


class Mutation(Type):
    login = Field(LoginResNode, args={'tipo': UserTypeNode, 'email': String, 'senha': String})
    create_admin_sistema = Field(CreateResNode, args={'nome': String, 'email': String, 'senha': String})
