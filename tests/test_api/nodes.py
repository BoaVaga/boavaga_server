from sgqlc.types import String, Type, Boolean, ID, Field, Enum, Scalar

from src.enums import EstadosEnum


class Upload(Scalar):
    pass


class UserTypeNode(Enum):
    __choices__ = ('SISTEMA', 'ESTACIONAMENTO')


class EstadosEnumNode(Enum):
    __choices__ = ['TEST', *EstadosEnum.__members__.keys()]


class EnderecoNode(Type):
    logradouro = String
    estado = EstadosEnumNode
    cidade = String
    bairro = String
    numero = String
    cep = String

    def __to_graphql_input__(self, indent, indent_string):
        _attrs = ('logradouro', 'estado', 'cidade', 'bairro', 'numero', 'cep')
        _str = '{\n'

        for attr in _attrs:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                v = getattr(self, attr)
                _str += f'{attr}:"{v}"' if attr != 'estado' else f'{attr}:{v}\n'

        _str += '}'
        return _str
        # return f'{{\nlogradouro: "{self.logradouro}"\n estado: {self.estado}\n cidade: "{self.cidade}"\n ' \
        #        f'bairro: "{self.bairro}"\n numero: "{self.numero}"\n cep: "{self.cep}"}}'


class AdminSistemaNode(Type):
    id = ID
    nome = String
    email = String


class AdminEstacioNode(Type):
    id = ID
    email = String


class PedidoCadastroNode(Type):
    id = ID
    nome = String
    telefone = String
    endereco = EnderecoNode
    foto = String
    admin_estacio = AdminEstacioNode


class CreateResNode(Type):
    success = Boolean
    error = String
    admin_sistema = AdminSistemaNode


class LoginResNode(Type):
    success = Boolean
    error = String
    token = String


class PedidoCadastroResNode(Type):
    success = Boolean
    error = String
    pedido_cadastro = PedidoCadastroNode


class Mutation(Type):
    login = Field(LoginResNode, args={'tipo': UserTypeNode, 'email': String, 'senha': String})
    create_admin_sistema = Field(CreateResNode, args={'nome': String, 'email': String, 'senha': String})
    create_pedido_cadastro = Field(PedidoCadastroResNode, args={'nome': String, 'telefone': String,
                                                                'endereco': EnderecoNode, 'foto': Upload})
