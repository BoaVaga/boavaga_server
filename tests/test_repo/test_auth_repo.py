import datetime
import pathlib
import re
import unittest
from unittest.mock import MagicMock

from src.container import create_container
from src.enums import UserType
from src.models import AdminSistema, AdminEstacio
from src.models.senha_request import SenhaRequest
from src.repo import AuthRepo
from src.services import Crypto
from tests.factories import set_session, AdminSistemaFactory, AdminEstacioFactory
from tests.utils import make_general_db_setup, general_db_teardown, MockedCached, \
    make_mocked_cached_provider, make_engine, make_savepoint, singleton_provider


class TestAuthRepo(unittest.TestCase):
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

        self.crypto = self.container.crypto()
        self.email_sender = MagicMock()

        self.container.cached.override(make_mocked_cached_provider(self.container))
        self.container.crypto.override(singleton_provider(self.crypto))
        self.container.email_sender.override(singleton_provider(self.email_sender))

        self.cached: MockedCached = self.container.cached()

        self.repo = AuthRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)
        self.cached.clear_all()
        self.cached.close()

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

    def test_login_token_collision(self):
        token_char = ord('1')

        def fake_random_hex_string(size: int) -> str:
            nonlocal token_char

            s = chr(token_char) * (size * 2)
            token_char += 1

            return s

        self.crypto.random_hex_string = MagicMock()
        self.crypto.random_hex_string.side_effect = fake_random_hex_string

        success, token = self.repo.login(self.session, 'jorge@email.com', 'senha123', UserType.SISTEMA)
        self.assertEqual(True, success, f'Success should be True on 0. Error: {token}')
        self.assertEqual('1' * 32, token, 'Unexpected token on 0.')

        token_char = ord('1')

        success, token = self.repo.login(self.session, 'jorge@email.com', 'senha123', UserType.SISTEMA)
        self.assertEqual(True, success, f'Success should be True on 1. Error: {token}')
        self.assertNotEqual('1' * 32, token, 'Token should be different')

    def test_enviar_email_senha_ok(self):
        requests = [
            (UserType.SISTEMA, 'jorge@email.com', self.admin_sis[0]),
            (UserType.SISTEMA, 'maria@email.com', self.admin_sis[1]),
            (UserType.ESTACIONAMENTO, 'jorge@email.com', self.admin_estacio[0]),
            (UserType.ESTACIONAMENTO, 'joana@email.com', self.admin_estacio[1]),
        ]

        now = datetime.datetime.now().replace(second=0, microsecond=0)

        for i in range(len(requests)): 
            tipo, email, user = requests[i]
            success, error = self.repo.enviar_email_senha(self.session, email, tipo)

            self.assertIsNone(error, f'Error should be None on {i}')
            self.assertEqual(True, success, f'Success should be True on {i}')

            if tipo == UserType.SISTEMA:
                fattr, null_attr = SenhaRequest.admin_sistema_fk, 'admin_estacio_fk'
            else:
                fattr, null_attr = SenhaRequest.admin_estacio_fk, 'admin_sistema_fk'

            requests = self.session.query(SenhaRequest).filter(fattr == user.id).all()
            self.assertEqual(1, len(requests), f'Should create exactly one request on {i}')

            request = requests[0]
            self.assertIsNotNone(request.code, f'Should create a code on {i}')
            self.assertEqual(16, len(request.code), f'The length of the code should be 16 on {i}')
            self.assertIsNone(getattr(request, null_attr), f'{null_attr} should be None on {i}')
            self.assertEqual(now, request.data_cricao, f'Create date should match on {i}')

    def test_enviar_senha_twice(self):
        # TODO
        pass

    def test_enviar_senha_user_not_found(self):
        # TODO
        pass

    def _check_response(self, response, i):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn('login', response.json['data'], f'Base data should contain "login" on {i}')

        return response.json['data']['login']


if __name__ == '__main__':
    unittest.main()
