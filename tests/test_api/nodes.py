from sgqlc.types import String, Type, Boolean, ID, Field, Enum, Scalar, list_of, Int

from src.enums import EstadosEnum


class Upload(Scalar):
    pass


class Point(Scalar):
    def __to_graphql_input__(cls, value, indent=0, indent_string='  '):
        return ''.join(('"', str(cls), '"'))


class Time(Scalar):
    def __to_graphql_input__(cls, value, indent=0, indent_string='  '):
        return cls.hour * 3600 + cls.minute * 60


class Date(Scalar):
    def __to_graphql_input__(cls, value, indent=0, indent_string='  '):
        return ''.join(('"', cls.isoformat(), '"'))


class Decimal(Scalar):
    def __to_graphql_input__(cls, value, indent=0, indent_string='  '):
        return str(cls)


class UserTypeNode(Enum):
    __choices__ = ('SISTEMA', 'ESTACIONAMENTO')


class EstadosEnumNode(Enum):
    __choices__ = ['TEST', *EstadosEnum.__members__.keys()]


class EnderecoNode(Type):
    id = ID
    logradouro = String
    estado = EstadosEnumNode
    cidade = String
    bairro = String
    numero = String
    cep = String
    coordenadas = Point

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


class HorarioPadraoNode(Type):
    segundaAbr = Time
    segundaFec = Time
    tercaAbr = Time
    tercaFec = Time
    quartaAbr = Time
    quartaFec = Time
    quintaAbr = Time
    quintaFec = Time
    sextaAbr = Time
    sextaFec = Time
    sabadoAbr = Time
    sabadoFec = Time
    domingoAbr = Time
    domingoFec = Time


class ValorHoraNode(Type):
    id = ID
    valor = Decimal
    veiculo = String


class HorarioDivergenteNode(Type):
    id = ID
    data = Date
    hora_abr = Time
    hora_fec = Time


class EstacionamentoNode(Type):
    id = ID
    nome = String
    telefone = String
    endereco = EnderecoNode
    foto = String
    esta_suspenso = Boolean
    esta_aberto = Boolean
    cadastro_terminado = Boolean
    descricao = String
    qtd_vaga_livre = Int
    horario_padrao = HorarioPadraoNode
    valores_hora = list_of(ValorHoraNode)
    horas_divergentes = list_of(HorarioDivergenteNode)


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


class PedidoCadastroResListNode(Type):
    success = Boolean
    error = String
    pedidos_cadastro = list_of(PedidoCadastroNode)


class PedidoCadAcceptResNode(Type):
    success = Boolean
    error = String
    estacionamento = EstacionamentoNode


class Mutation(Type):
    login = Field(LoginResNode, args={'tipo': UserTypeNode, 'email': String, 'senha': String})
    create_admin_sistema = Field(CreateResNode, args={'nome': String, 'email': String, 'senha': String})
    create_pedido_cadastro = Field(PedidoCadastroResNode, args={'nome': String, 'telefone': String,
                                                                'endereco': EnderecoNode, 'foto': Upload})
    accept_pedido_cadastro = Field(PedidoCadAcceptResNode, args={'pedido_id': ID, 'coordenadas': Point})
    test_mut = Field(LoginResNode, args={'tempo': Time, 'data': Date, 'valor': Decimal, 'cord': Point})


class Query(Type):
    get_pedido_cadastro = Field(PedidoCadastroResNode, args={'pedido_id': ID})
    list_pedido_cadastro = Field(PedidoCadastroResListNode, args={'amount': Int, 'index': Int})
