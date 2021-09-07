import pathlib
import unittest

from src.container import create_container
from src.enums import UserType
from src.models import AdminSistema, AdminEstacio
from src.repo import AuthRepo
from src.services import Crypto
from tests.factory import set_session, AdminSistemaFactory, AdminEstacioFactory
from tests.utils import make_general_db_setup, general_db_teardown, MockedCached, \
    make_mocked_cached_provider, make_engine, make_savepoint


class TestAuthApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[2] / 'test.ini')
        cls.container = create_container(config_path)

        conn_string = str(cls.container.config.get('db')['conn_string'])
        cls.engine = make_engine(conn_string)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        set_session(self.session)  # Factories

        crypto = Crypto(is_testing=True, salt_rounds=12)
        senha = crypto.hash_password(b'senha123')

        self.admin_sis = [AdminSistemaFactory.create(nome='Jorge', email='jorge@email.com', senha=senha),
                          AdminSistemaFactory.create(nome='Maria', email='maria@email.com', senha=senha)]
        self.admin_estacio = [AdminEstacioFactory.create(email='jorge@email.com', senha=senha),
                              AdminEstacioFactory.create(email='joana@email.com', senha=senha)]
        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.container.cached.override(make_mocked_cached_provider(self.container))
        self.cached: MockedCached = self.container.cached()

        self.repo = AuthRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)
        self.cached.clear_all()

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        admin_estacio = self.session.query(AdminEstacio).all()

        self.assertEqual(self.admin_sis, admin_sis)
        self.assertEqual(self.admin_estacio, admin_estacio)

    def test_login_ok(self):
        requests = [
            (UserType.SISTEMA, 'jorge@email.com'),
            (UserType.SISTEMA, 'maria@email.com'),
            (UserType.ESTACIONAMENTO, 'jorge@email.com'),
            (UserType.ESTACIONAMENTO, 'joana@email.com'),
        ]

        all_tokens = set()

        for i in range(len(requests)):
            tipo, email = requests[i]

            success, error_or_token = self.repo.login(self.session, email, 'senha123', tipo)
            self.assertEqual(True, success, f'Success should be True on {i}. Error: {error_or_token}')
            self.assertIsNotNone(error_or_token, f'Token should not be null on {i}')

            self.assertNotIn(error_or_token, all_tokens, f'The tokens should be unique. Error on {i}')
            all_tokens.add(error_or_token)

    def test_login_senha_errada(self):
        requests = [
            (UserType.SISTEMA, 'jorge@email.com'),
            (UserType.SISTEMA, 'maria@email.com'),
            (UserType.ESTACIONAMENTO, 'jorge@email.com'),
            (UserType.ESTACIONAMENTO, 'joana@email.com'),
        ]

        for i in range(len(requests)):
            tipo, email = requests[i]

            success, error = self.repo.login(self.session, email, 'senha_errada', tipo)

            self.assertEqual('senha_incorreta', error, f'Error should be "senha_incorreta" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_login_email_nao_encontrado(self):
        requests = [
            (UserType.SISTEMA, 'jorge@un.com'),
            (UserType.SISTEMA, 'maria@un.com'),
            (UserType.ESTACIONAMENTO, 'jorge@un.com'),
            (UserType.ESTACIONAMENTO, 'joana@un.com'),
        ]

        for i in range(len(requests)):
            tipo, email = requests[i]

            success, error = self.repo.login(self.session, email, 'senha123', tipo)

            self.assertEqual('email_nao_encontrado', error, f'Error should be "email_nao_encontrado" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def _check_response(self, response, i):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn('login', response.json['data'], f'Base data should contain "login" on {i}')

        return response.json['data']['login']


if __name__ == '__main__':
    unittest.main()
