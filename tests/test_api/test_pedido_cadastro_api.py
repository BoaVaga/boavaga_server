import json
import pathlib
import unittest
from collections import namedtuple
from io import BytesIO
from unittest.mock import Mock

from dependency_injector.providers import Singleton
from sgqlc.operation import Operation
from sgqlc.types import Variable, Arg, non_null

from src.app import create_app
from src.container import create_container
from src.enums import UploadStatus
from src.models import PedidoCadastro, Endereco, Upload
from src.repo.repo_container import create_repo_container
from tests.factories import BaseEnderecoFactory
from tests.test_api.nodes import Mutation, Upload as UploadType
from tests.utils import make_engine, make_mocked_cached_provider, make_general_db_setup, get_adm_estacio_login, \
    make_savepoint, general_db_teardown


class TestPedidoCadastroApi(unittest.TestCase):
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
        self.container.cached.override(make_mocked_cached_provider(self.container))

        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        self.user, self.user_sess, self.login_success, self.login_token = \
            get_adm_estacio_login(self.repo_container, self.container.crypto(), self.session)

        make_savepoint(self.conn, self.session)

        self.repo_container.pedido_cadastro_repo.override(Singleton(Mock))
        self.repo = self.repo_container.pedido_cadastro_repo()

        self.app = create_app(self.container, self.repo_container)
        self.client = self.app.test_client(use_cookies=False)

        self.client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {self.login_token}'

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

        self.container.cached().clear_all()

    def test_setup(self):
        self.assertEqual(True, self.login_success, f'Success should be True. Error: {self.login_token}')
        self.assertIsNotNone(self.login_token, 'Login token should not be null')

    def test_create_ok(self):
        nome, telefone = 'Estacio Teste', '+5512345678901'
        endereco = BaseEnderecoFactory.create()
        endereco_dct = endereco.to_dict()
        foto_stream = BytesIO(b'abc')
        foto = Upload(nome_arquivo='abc.jpg', sub_dir='foto_estacio', status=UploadStatus.CONCLUIDO)
        foto_url = 'foto_estacio/abc.jpg'

        self.repo.create.return_value = (True, PedidoCadastro(id=341, nome=nome, telefone=telefone, endereco=endereco,
                                                              foto=foto))

        mutation = Operation(Mutation, variables={'foto': Arg(non_null(UploadType))})
        mutation.create_pedido_cadastro(nome=nome, telefone=telefone, endereco=endereco_dct, foto=Variable('foto'))

        js_str = json.dumps({'variables': {'foto': None}, 'query': mutation.__to_graphql__(auto_select_depth=5)})
        response = self.client.post('/graphql', content_type='multipart/form-data',
                                    data={'operations': js_str, 'map': '{"0":["variables.foto"]}',
                                          '0': (foto_stream, '0')})
        data = self._check_response(response, 'createPedidoCadastro')

        self.assertIsNone(data['error'], f'Error should be null')
        self.assertEqual(True, data['success'], f'Success should be True')

        pedido = data['pedidoCadastro']

        self.assertIsNotNone(pedido, 'Pedido should not be null')
        self.assertEqual('341', pedido['id'], 'IDs should match')
        self.assertEqual(nome, pedido['nome'], 'Nomes should match')
        self.assertEqual(telefone, pedido['telefone'], 'Telefones should match')

        endereco_ret = pedido['endereco']
        self._check_endereco(endereco, endereco_ret)

        self.assertEqual(foto_url, pedido['foto'], 'Fotos url should match')

    def test_create_errors(self):
        end_dct = BaseEnderecoFactory.create().to_dict()

        for error in ['nome_muito_grande', 'sem_permissao', 'telefone_formato_invalido',
                      'telefone_sem_cod_internacional', 'telefone_muito_grande', 'foto_formato_invalido',
                      'upload_error', 'limite_pedido_atingido']:
            foto_stream = BytesIO(b'abc')
            self.repo.create.return_value = (False, error)

            mutation = Operation(Mutation, variables={'foto': Arg(non_null(UploadType))})
            mutation.create_pedido_cadastro(nome='Teste', telefone='+5511981845155', endereco=end_dct,
                                            foto=Variable('foto'))

            js_str = json.dumps({'variables': {'foto': None}, 'query': mutation.__to_graphql__(auto_select_depth=5)})
            response = self.client.post('/graphql', content_type='multipart/form-data',
                                        data={'operations': js_str, 'map': '{"0":["variables.foto"]}',
                                              '0': (foto_stream, '0')})
            data = self._check_response(response, 'createPedidoCadastro')

            self.assertEqual(error, data['error'], f'Errors should match on "{error}"')
            self.assertEqual(False, data['success'], f'Should return False on "{error}')

    def test_endereco_validation_fail(self):
        caso_teste = namedtuple('CasoTeste', 'attr values')
        _attrs = ('logradouro', 'cidade', 'bairro', 'numero', 'cep')

        cases = {f'end_{attr}_vazio': caso_teste(attr, ('', '         ')) for attr in _attrs}
        max_len_attr = {
            'logradouro': 101, 'cidade': 51, 'bairro': 51, 'numero': 11, 'cep': 9
        }
        cases.update({f'end_{attr}_muito_grande': caso_teste(attr, ['A' * v]) for attr, v in max_len_attr.items()})

        base_end_dct = BaseEnderecoFactory.create().to_dict()
        self.repo.create.return_value = (False, 'should_not_call_create')

        for error, caso in cases.items():
            for i in range(len(caso.values)):
                foto_stream = BytesIO(b'abc')
                end_dct = dict(base_end_dct)

                if caso.values[i] is not None:
                    end_dct[caso.attr] = caso.values[i]
                else:
                    del end_dct[caso.attr]

                mutation = Operation(Mutation, variables={'foto': Arg(non_null(UploadType))})
                mutation.create_pedido_cadastro(nome='Teste', telefone='+5511981845155', endereco=end_dct,
                                                foto=Variable('foto'))

                js_str = json.dumps({'variables': {'foto': None}, 'query': str(mutation)})
                response = self.client.post('/graphql', content_type='multipart/form-data',
                                            data={'operations': js_str, 'map': '{"0":["variables.foto"]}',
                                                  '0': (foto_stream, '0')})

                data = self._check_response(response, 'createPedidoCadastro')

                self.assertEqual(error, data['error'], f'Errors should match on "{error}:{i}"')
                self.assertEqual(False, data['success'], f'Should return False on "{error}:{i}')

    def _check_response(self, response, group, i=0):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn(group, response.json['data'], f'Base data should contain "{group}" on {i}')

        return response.json['data'][group]

    def _check_endereco(self, endereco: Endereco, ret, i=0):
        end = Endereco.from_dict(ret)
        end.id = endereco.id

        self.assertEqual(endereco, end, f'Enderecos should match on {i}')


if __name__ == '__main__':
    unittest.main()
