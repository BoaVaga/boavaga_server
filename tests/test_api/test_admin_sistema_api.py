import pathlib
import unittest
from unittest.mock import Mock

from dependency_injector.providers import Singleton
from sgqlc.operation import Operation
from sgqlc.types import String, Type, Boolean, ID, Field

from src.app import create_app
from src.container import create_container
from src.models import AdminSistema
from src.repo.repo_container import create_repo_container


class AdminSistemaNode(Type):
    id = ID
    nome = String
    email = String


class CreateResNode(Type):
    success = Boolean
    error = String
    admin_sistema = AdminSistemaNode


class Mutation(Type):
    create_admin_sistema = Field(CreateResNode, args={'nome': String, 'email': String, 'senha': String})


class TestAdminSistemaApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[2] / 'test.ini')
        cls.container = create_container(config_path)
        cls.repo_container = create_repo_container(config_path)

    def setUp(self) -> None:
        self.repo_container.admin_sistema_repo.override(Singleton(Mock))
        self.repo = self.repo_container.admin_sistema_repo()

        self.app = create_app(self.container, self.repo_container)
        self.client = self.app.test_client(use_cookies=False)

    def test_create_ok(self):
        self.repo.create_admin.return_value = (True, AdminSistema(id=123, nome='Pedrinho', email='pedrinho@un.com'))

        mutation = Operation(Mutation)
        mutation.create_admin_sistema(nome='Pedrinho', email='pedrinho@un.com', senha='pedrao123')

        response = self.client.post('/graphql', json={'query': str(mutation)})
        data = self._check_response(response, 'createAdminSistema')

        self.assertIsNone(data['error'], f'Error should be null')
        self.assertEqual(True, data['success'], f'Success should be True')
        admin = data['adminSistema']

        self.assertIsNotNone(admin, 'Admin should not be null')
        self.assertEqual('123', admin['id'], 'IDs should match')
        self.assertEqual('Pedrinho', admin['nome'], 'Names should match')
        self.assertEqual('pedrinho@un.com', admin['email'], 'Emails should match')

    def test_create_errors(self):
        for error in ['email_ja_cadastrado', 'Random exception']:
            self.repo.create_admin.return_value = (False, error)

            mutation = Operation(Mutation)
            mutation.create_admin_sistema(nome='Pedrinho', email='pedrinho@un.com', senha='pedrao123')

            response = self.client.post('/graphql', json={'query': str(mutation)})
            data = self._check_response(response, 'createAdminSistema')

            self.assertEqual(error, data['error'], f'Errors should match on "{error}"')
            self.assertEqual(False, data['success'], f'Should return False on "{error}')

    def _check_response(self, response, group, i=0):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn(group, response.json['data'], f'Base data should contain "{group}" on {i}')

        return response.json['data'][group]


if __name__ == '__main__':
    unittest.main()
