import random
from uuid import uuid4

import factory
import factory.fuzzy
import faker.providers.phone_number.pt_BR

from src.enums import EstadosEnum, UploadStatus
from src.models import AdminSistema, AdminEstacio, Endereco, Upload, PedidoCadastro
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


factory.Faker.add_provider(SimplePhoneProvider, locale='pt_BR')


def _random_password():
    return crypto.hash_password(random_string(10).encode('ascii'))


def _from_enum(enum):
    def clb():
        return random.choice(list(enum))

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


_ALL_FACTORIES = (AdminSistemaFactory, AdminEstacioFactory, UploadFactory, EnderecoFactory, PedidoCadastroFactory)


def set_session(session):
    for fac in _ALL_FACTORIES:
        fac._meta.sqlalchemy_session = session


def teardown_factories():
    for fac in _ALL_FACTORIES:
        fac.reset_sequence()
