import pathlib
import unittest
from uuid import uuid1
from unittest.mock import Mock

from dependency_injector.providers import Singleton
from sgqlc.operation import Operation

from src.app import create_app
from src.container import create_container
from src.repo.repo_container import create_repo_container
from tests.test_api.nodes import Mutation, UserTypeNode


class TestAuthApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[2] / 'test.ini')
        cls.container = create_container(config_path)
        cls.repo_container = create_repo_container(config_path)

    def setUp(self) -> None:
        self.repo_container.auth_repo.override(Singleton(Mock))
        self.repo = self.repo_container.auth_repo()

        self.app = create_app(self.container, self.repo_container)
        self.client = self.app.test_client(use_cookies=False)

    def test_login_ok(self):
        def fake_login(*_, **__):
            return True, uuid1()

        self.repo.login.side_effect = fake_login

        requests = [
            (UserTypeNode('SISTEMA'), 'jorge@email.com'),
            (UserTypeNode('ESTACIONAMENTO'), 'jorge@email.com'),
        ]

        for i in range(len(requests)):
            tipo, email = requests[i]

            mutation = Operation(Mutation)
            mutation.login(tipo=tipo, email=email, senha='senha123')

            response = self.client.post('/graphql', json={'query': str(mutation)})
            data = self._check_response(response, i)

            self.assertIsNone(data['error'], f'Error should be null on {i}')
            self.assertEqual(True, data['success'], f'Success should be True on {i}')
            self.assertIsNotNone(data['token'], f'Token should not be null on {i}')

    def test_login_errors(self):
        requests = [
            (UserTypeNode('SISTEMA'), 'jorge@email.com'),
            (UserTypeNode('ESTACIONAMENTO'), 'jorge@email.com'),
        ]

        for error in ['senha_incorreta', 'email_nao_encontrado', 'random_ex_122131234']:
            self.repo.login.return_value = (False, error)

            for i in range(len(requests)):
                tipo, email = requests[i]

                mutation = Operation(Mutation)
                mutation.login(tipo=tipo, email=email, senha='senha123')

                response = self.client.post('/graphql', json={'query': str(mutation)})

                info = f'{error}.{i}'
                data = self._check_response(response, info)

                self.assertEqual(error, data['error'], f'Error should be "{error}" on {info}')
                self.assertEqual(False, data['success'], f'Success should be False on {info}')
                self.assertIsNone(data['token'], f'Token should be null on {info}')

    def _check_response(self, response, i):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn('login', response.json['data'], f'Base data should contain "login" on {i}')

        return response.json['data']['login']


if __name__ == '__main__':
    unittest.main()
