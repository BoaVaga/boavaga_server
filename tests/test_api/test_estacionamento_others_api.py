import logging
import pathlib
import unittest
from unittest.mock import Mock

from dependency_injector.providers import Singleton
from sgqlc.operation import Operation

from src.app import create_app
from src.container import create_container
from src.repo.repo_container import create_repo_container
from tests.test_api.nodes import Mutation
from tests.utils import make_engine, make_mocked_cached_provider, make_general_db_setup, get_adm_estacio_login, \
    make_savepoint, general_db_teardown, disable_email_sender


class TestEstacionamentoOthersApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[2] / 'test.ini')
        cls.container = create_container(config_path)
        disable_email_sender(cls.container)
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
            get_adm_estacio_login(self.repo_container, self.container.crypto(), self.session)

        make_savepoint(self.conn, self.session)

        self.repo_container.estacionamento_others_repo.override(Singleton(Mock))
        self.repo = self.repo_container.estacionamento_others_repo()

        self.app = create_app(self.container, self.repo_container)
        self.client = self.app.test_client(use_cookies=False)

        self.client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {self.login_token}'

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

        self.container.cached().clear_all()
        self.container.cached().close()

    def test_setup(self):
        self.assertEqual(True, self.login_success, f'Success should be True. Error: {self.login_token}')
        self.assertIsNotNone(self.login_token, 'Login token should not be null')

    def test_create_ok(self):
        self.repo.atualizar_vagas_livres.return_value = (True, None)

        mutation = Operation(Mutation)
        mutation.atualizar_qtd_vaga_livre(num_vaga=10)

        response = self.client.post('/graphql', json={'query': mutation.__to_graphql__(auto_select_depth=5)})
        data = self._check_response(response, 'atualizarQtdVagaLivre')

        self.assertIsNone(data['error'], 'Error should be None')
        self.assertEqual(True, data['success'], 'Success should be True')

    def test_create_errors(self):
        for error in ['quantia_negativa', 'quantia_maior_que_total', 'sem_estacionamento', 'sem_permissao', None]:
            self.repo.atualizar_vagas_livres.reset_mock()
            if error is None:
                self.repo.atualizar_vagas_livres.side_effect = Exception('Random Error')
                error = 'erro_desconhecido'
            else:
                self.repo.atualizar_vagas_livres.return_value = (False, error)

            mutation = Operation(Mutation)
            mutation.atualizar_qtd_vaga_livre(num_vaga=10)

            response = self.client.post('/graphql', json={'query': str(mutation)})
            data = self._check_response(response, 'atualizarQtdVagaLivre')

            self.assertEqual(error, data['error'], f'Error should be "{error}"')
            self.assertEqual(False, data['success'], f'Success should be False on "{error}"')

    def _check_response(self, response, group, i=0):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn(group, response.json['data'], f'Base data should contain "{group}" on {i}')

        return response.json['data'][group]


if __name__ == '__main__':
    unittest.main()
