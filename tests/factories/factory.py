import random
from decimal import Decimal
from uuid import uuid4

import factory
import factory.fuzzy
import faker.providers.phone_number.pt_BR
import faker.providers.date_time

from src.enums import EstadosEnum, UploadStatus
from src.models import AdminSistema, AdminEstacio, Endereco, Upload, PedidoCadastro, Estacionamento, HorarioPadrao, \
    ValorHora, Veiculo, HorarioDivergente
from src.services import Crypto
from src.utils import random_string

crypto = Crypto(True, 12)


class SimplePhoneProvider(faker.providers.phone_number.pt_BR.Provider):
    def cellphone_number(self, formatted=True):
        _s = super().cellphone_number()
        if formatted:
            return _s
        else:
            return _s.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')


class CustomTimeProvider(faker.providers.date_time.Provider):
    def time_object(self, **kwargs):
        _t = super().time_object()
        _kw = {k: v for k, v in kwargs.items() if v is not None}

        return _t.replace(**_kw)


factory.Faker.add_provider(SimplePhoneProvider, locale='pt_BR')
factory.Faker.add_provider(CustomTimeProvider)


def _random_password():
    return crypto.hash_password(random_string(10).encode('ascii'))


def _from_enum(enum):
    def clb():
        return random.choice(list(enum))

    return clb


def _random_int(a, b):
    def clb():
        return random.randint(a, b)

    return clb


def _random_decimal(a, b):
    def clb():
        return Decimal(random.randint(a, b))

    return clb


class AdminSistemaFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    nome = factory.Faker('name')
    email = factory.Faker('email')
    senha = factory.LazyFunction(_random_password)

    class Meta:
        model = AdminSistema
        sqlalchemy_session_persistence = None


class AdminEstacioFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    email = factory.Faker('email')
    senha = factory.LazyFunction(_random_password)
    admin_mestre = False

    class Meta:
        model = AdminEstacio
        sqlalchemy_session_persistence = None


class UploadFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    nome_arquivo = factory.LazyFunction(uuid4)
    sub_dir = factory.fuzzy.FuzzyText(length=10)
    status = factory.LazyFunction(_from_enum(UploadStatus))

    class Meta:
        model = Upload
        sqlalchemy_session_persistence = None


class EnderecoFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    logradouro = factory.Faker('street_name', locale='pt_BR')
    estado = factory.LazyFunction(_from_enum(EstadosEnum))
    cidade = factory.Faker('city', locale='pt_BR')
    bairro = factory.Faker('bairro', locale='pt_BR')
    numero = factory.Faker('building_number', locale='pt_BR')
    cep = factory.Faker('postcode', locale='pt_BR', formatted=False)
    coordenadas = None

    class Meta:
        model = Endereco
        sqlalchemy_session_persistence = None


class PedidoCadastroFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    nome = factory.Faker('name')
    telefone = factory.Faker('cellphone_number', locale='pt_BR', formatted=False)
    endereco = factory.SubFactory(EnderecoFactory)
    foto = factory.SubFactory(UploadFactory)
    admin_estacio = factory.SubFactory(AdminEstacioFactory)

    endereco_fk = factory.SelfAttribute('endereco.id')
    foto_fk = factory.SelfAttribute('foto.id')
    admin_estacio_fk = factory.SelfAttribute('admin_estacio.id')

    class Meta:
        model = PedidoCadastro
        sqlalchemy_session_persistence = None


class HorarioPadraoFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    segunda_abr = None
    segunda_fec = None
    terca_abr = None
    terca_fec = None
    quarta_abr = None
    quarta_fec = None
    quinta_abr = None
    quinta_fec = None
    sexta_abr = None
    sexta_fec = None
    sabado_abr = None
    sabado_fec = None
    domingo_abr = None
    domingo_fec = None

    class Meta:
        model = HorarioPadrao
        sqlalchemy_session_persistence = None


class VeiculoFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    nome = factory.Faker('name', locale='pt_BR')

    class Meta:
        model = Veiculo
        sqlalchemy_session_persistence = None


class ValorHoraFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    valor = factory.LazyFunction(_random_decimal(10, 100))
    veiculo = factory.SubFactory(VeiculoFactory)
    estacionamento = None

    veiculo_fk = factory.SelfAttribute('veiculo.id')
    estacio_fk = factory.SelfAttribute('estacionamento.id')

    class Meta:
        model = ValorHora
        sqlalchemy_session_persistence = None


class HorarioDivergenteFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    data = factory.Faker('date_between')
    hora_abr = factory.Faker('time_object', second=0)
    hora_fec = factory.Faker('time_object', second=0)
    estacionamento = None

    estacio_fk = factory.SelfAttribute('estacionamento.id')

    class Meta:
        model = HorarioDivergente
        sqlalchemy_session_persistence = None


class EstacionamentoFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x + 1)
    nome = factory.Faker('name')
    telefone = factory.Faker('cellphone_number', locale='pt_BR', formatted=False)
    esta_suspenso = False
    esta_aberto = True
    cadastro_terminado = True
    descricao = factory.Faker('paragraph')
    qtd_vaga_livre = factory.LazyFunction(_random_int(0, 30))

    endereco = factory.SubFactory(EnderecoFactory)
    foto = factory.SubFactory(UploadFactory)
    horario_padrao = factory.SubFactory(HorarioPadraoFactory)

    endereco_fk = factory.SelfAttribute('endereco.id')
    foto_fk = factory.SelfAttribute('foto.id')
    horap_fk = factory.SelfAttribute('horario_padrao.id')

    @factory.post_generation
    def valores_hora(self, create, extracted, **kwargs):
        if extracted:
            assert isinstance(extracted, int)
            if create:
                valores = ValorHoraFactory.create_batch(size=extracted, estacionamento=self, **kwargs)
                self.valores_hora.append(valores)
            else:
                ValorHoraFactory.build_batch(size=extracted, estacionamento=self, **kwargs)

    @factory.post_generation
    def horas_divergentes(self, create, extracted, **kwargs):
        if extracted:
            assert isinstance(extracted, int)
            if create:
                horas = HorarioDivergenteFactory.create_batch(size=extracted, estacionamento=self, **kwargs)
                self.valores_hora.append(horas)
            else:
                HorarioDivergenteFactory.build_batch(size=extracted, estacionamento=self, **kwargs)

    class Meta:
        model = Estacionamento
        sqlalchemy_session_persistence = None


_ALL_FACTORIES = (AdminSistemaFactory, AdminEstacioFactory, UploadFactory, EnderecoFactory, PedidoCadastroFactory,
                  EstacionamentoFactory, HorarioPadraoFactory, ValorHoraFactory, VeiculoFactory,
                  HorarioDivergenteFactory)


def set_session(session):
    for fac in _ALL_FACTORIES:
        fac._meta.sqlalchemy_session = session


def teardown_factories():
    for fac in _ALL_FACTORIES:
        fac.reset_sequence()
