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
    admin_mestre = Boolean


class PedidoCadastroNode(Type):
    id = ID
    nome = String
    telefone = String
    endereco = EnderecoNode
    foto = String
    admin_estacio = AdminEstacioNode


class HorarioPadraoNode(Type):
    segunda_abr = Time
    segunda_fec = Time
    terca_abr = Time
    terca_fec = Time
    quarta_abr = Time
    quarta_fec = Time
    quinta_abr = Time
    quinta_fec = Time
    sexta_abr = Time
    sexta_fec = Time
    sabado_abr = Time
    sabado_fec = Time
    domingo_abr = Time
    domingo_fec = Time


class ValorHoraNode(Type):
    id = ID
    valor = Decimal
    veiculo = String


class ValorHoraInputNode(Type):
    valor = Decimal
    veiculo_id = ID


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
    total_vaga = Int
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


class EstacioCadResNode(Type):
    success = Boolean
    error = String
    estacionamento = EstacionamentoNode


class SimpleResponseNode(Type):
    success = Boolean
    error = String


class Mutation(Type):
    login = Field(LoginResNode, args={'tipo': UserTypeNode, 'email': String, 'senha': String})
    create_admin_sistema = Field(CreateResNode, args={'nome': String, 'email': String, 'senha': String})
    create_pedido_cadastro = Field(PedidoCadastroResNode, args={'nome': String, 'telefone': String,
                                                                'endereco': EnderecoNode, 'foto': Upload})
    accept_pedido_cadastro = Field(EstacioCadResNode, args={'pedido_id': ID, 'coordenadas': Point})
    finish_estacionamento_cadastro = Field(EstacioCadResNode,
                                           args={'total_vaga': Int, 'horario_padrao': HorarioPadraoNode,
                                                 'valores_hora': list_of(ValorHoraInputNode), 'estacio_id': ID,
                                                 'descricao': String})
    atualizar_qtd_vaga_livre = Field(SimpleResponseNode, args={'num_vaga': Int})


class Query(Type):
    get_pedido_cadastro = Field(PedidoCadastroResNode, args={'pedido_id': ID})
    list_pedido_cadastro = Field(PedidoCadastroResListNode, args={'amount': Int, 'index': Int})
