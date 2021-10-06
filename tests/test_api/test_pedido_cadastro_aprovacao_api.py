import logging
import pathlib
import unittest
from unittest.mock import Mock

from dependency_injector.providers import Singleton

from src.app import create_app
from src.container import create_container
from src.repo.repo_container import create_repo_container
from tests.utils import general_db_teardown, make_savepoint, get_adm_sistema_login, make_general_db_setup, \
    make_mocked_cached_provider, make_engine


class TestAdminSistemaApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[2] / 'test.ini')
        cls.container = create_container(config_path)
        cls.repo_container = create_repo_container(config_path)

        conn_string = str(cls.container.config.get('db')['conn_string'])
        cls.engine = make_engine(conn_string)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        logging.basicConfig(level=logging.FATAL)
        self.container.cached.override(make_mocked_cached_provider(self.container))

        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        self.user, self.user_sess, self.login_success, self.login_token = \
            get_adm_sistema_login(self.repo_container, self.container.crypto(), self.session)

        make_savepoint(self.conn, self.session)

        self.repo_container.pedido_cadastro_aprovacao_repo.override(Singleton(Mock))
        self.repo = self.repo_container.pedido_cadastro_aprovacao_repo()

        self.app = create_app(self.container, self.repo_container)
        self.client = self.app.test_client(use_cookies=False)

        self.client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {self.login_token}'

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

        self.container.cached().clear_all()

    def test_setup(self):
        self.assertEqual(True, self.login_success, f'Success should be True. Error: {self.login_token}')
        self.assertIsNotNone(self.login_token, 'Login token should not be null')


if __name__ == '__main__':
    unittest.main()
