import factory

from src.models import AdminSistema, AdminEstacio
from src.services import Crypto
from src.utils import random_string

crypto = Crypto(True, 12)


def _random_password():
    return crypto.hash_password(random_string(10).encode('ascii'))


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


_ALL_FACTORIES = (AdminSistemaFactory, AdminEstacioFactory)


def set_session(session):
    for fac in _ALL_FACTORIES:
        fac._meta.sqlalchemy_session = session


def teardown_factories():
    for fac in _ALL_FACTORIES:
        fac.reset_sequence()
