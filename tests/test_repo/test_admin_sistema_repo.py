import pathlib
import unittest

from src.container import create_container
from src.models import AdminSistema
from src.repo import AdminSistemaRepo
from src.services import Crypto
from tests.factory import set_session, AdminSistemaFactory
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

        self.crypto = Crypto(is_testing=True, salt_rounds=12)
        senha = self.crypto.hash_password(b'outraSenha')

        self.admin_sis = [AdminSistemaFactory.create(nome='Jorge', email='jorge@email.com', senha=senha),
                          AdminSistemaFactory.create(nome='Maria', email='maria@email.com', senha=senha)]
        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.container.cached.override(make_mocked_cached_provider(self.container))
        self.cached: MockedCached = self.container.cached()

        self.repo = AdminSistemaRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

        self.cached.clear_all()

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        self.assertEqual(self.admin_sis, admin_sis)

    def test_create_ok(self):
        requests = [
            ('Jorge', 'jorge12@email.com', 'matheus12'),
            ('Joaquim', 'joaquim@email.com', 'joaquim12'),
            ('Fernanda', 'fernanda@email.com', 'fernanda12'),
            ('Mariana', 'mariana@email.com', 'mariana12'),
        ]

        for i in range(len(requests)):
            nome, email, senha = requests[i]

            success, error_or_admin = self.repo.create_admin(self.session, nome, email, senha)
            self.assertEqual(True, success, f'Success should be True on {i}. Error: {error_or_admin}')
            self.assertIsNotNone(error_or_admin, f'Admin should not be null on {i}')

            self.assertEqual(nome, error_or_admin.nome, f'Name does not match on {i}')
            self.assertEqual(email, error_or_admin.email, f'Email does not match on {i}')
            self.assertEqual(True, self.crypto.check_password(senha.encode('utf8'), error_or_admin.senha),
                             f'Senha does not match on {i}')

    def test_create_email_already_exists(self):
        requests = [
            ('Jorge', 'jorge@email.com', 'senha123'),
            ('Maria', 'maria@email.com', 'maria123'),
        ]

        for i in range(len(requests)):
            nome, email, senha = requests[i]

            success, error = self.repo.create_admin(self.session, nome, email, senha)

            self.assertEqual('email_ja_cadastrado', error, f'Error should be "email_ja_cadastrado" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def _check_response(self, response, i):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn('login', response.json['data'], f'Base data should contain "login" on {i}')

        return response.json['data']['login']


if __name__ == '__main__':
    unittest.main()
