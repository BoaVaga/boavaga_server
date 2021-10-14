import logging
import pathlib
import unittest
from typing import List
from unittest.mock import Mock

from dependency_injector.providers import Singleton

from src.app import create_app
from src.container import create_container
from src.models import Endereco, PedidoCadastro, AdminEstacio
from src.repo.repo_container import create_repo_container
from tests.factories import PedidoCadastroFactory
from tests.utils import make_engine, make_mocked_cached_provider, make_general_db_setup, get_adm_estacio_login, \
    make_savepoint, general_db_teardown


class BaseTestPedidoCadastroApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[3] / 'test.ini')
        cls.container = create_container(config_path)
        cls.repo_container = create_repo_container(config_path)

        conn_string = str(cls.container.config.get('db')['conn_string'])
        cls.engine = make_engine(conn_string)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        logging.basicConfig(level=logging.FATAL)
        self.maxDiff = 5000

        self.container.cached.override(make_mocked_cached_provider(self.container))

        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        self.user, self.user_sess, self.login_success, self.login_token = \
            get_adm_estacio_login(self.repo_container, self.container.crypto(), self.session)

        make_savepoint(self.conn, self.session)

        self.repo_container.pedido_cadastro_crud_repo.override(Singleton(Mock))
        self.repo = self.repo_container.pedido_cadastro_crud_repo()

        self.app = create_app(self.container, self.repo_container)
        self.client = self.app.test_client(use_cookies=False)

        self.pedidos = PedidoCadastroFactory.build_batch(10)

        self.client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {self.login_token}'

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

        self.container.cached().clear_all()
        self.container.cached().close()

    def test_setup(self):
        self.assertEqual(True, self.login_success, f'Success should be True. Error: {self.login_token}')
        self.assertIsNotNone(self.login_token, 'Login token should not be null')

    def check_response(self, response, group, i=0):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn(group, response.json['data'], f'Base data should contain "{group}" on {i}')

        return response.json['data'][group]

    def assert_endereco_equal(self, endereco: Endereco, ret, i='0'):
        end = Endereco.from_dict(ret)
        end.id = endereco.id

        self.assertEqual(endereco, end, f'Enderecos should match on {i}')

    def assert_pedido_equal(self, pedido: PedidoCadastro, ret, i='0', msg=None):
        dct = dict(ret)
        dct['id'] = int(dct['id'])

        endereco, admin_estacio = None, None

        if 'endereco' in dct:
            endereco = Endereco.from_dict(dct['endereco'])
            dct['endereco_fk'] = endereco.id
        if 'adminEstacio' in dct:
            d = dct['adminEstacio']
            admin_estacio = AdminEstacio(id=int(d['id']), email=d['email'], senha=pedido.admin_estacio.senha,
                                         admin_mestre=d['adminMestre'])
            dct['admin_estacio_fk'] = admin_estacio.id

            del dct['adminEstacio']

        pedido.foto_fk = None
        foto_str = str(pedido.foto)

        p_ret = PedidoCadastro(**dct)
        if msg is not None:
            self.assertEqual(pedido, p_ret, msg)
            self.assertEqual(foto_str, dct['foto'], msg)
            self.assertEqual(pedido.endereco, endereco, msg)
            self.assertEqual(pedido.admin_estacio, admin_estacio, msg)
        else:
            return pedido == p_ret and foto_str == dct['foto'] and pedido.endereco == endereco and pedido.admin_estacio == admin_estacio

    def assert_count_equal_pedidos(self, pedidos: List[PedidoCadastro], rets: List[dict], msg: str):
        already_checked = set()
        not_found_list_1 = set()

        self.assertEqual(len(pedidos), len(rets), msg.format('Length of lists is different'))
        for i in range(len(pedidos)):
            pedido = pedidos[i]

            for j in range(len(rets)):
                if self.assert_pedido_equal(pedido, rets[j]):
                    if j not in already_checked:
                        already_checked.add(j)
                        break
            else:
                not_found_list_1.add(i)

        not_found_list_2 = {i for i in range(len(rets)) if i not in already_checked}

        if len(not_found_list_1) > 0 or len(not_found_list_2) > 0:
            self.fail(msg.format(f'Indexes of the first list not found: {not_found_list_1}.\n'
                                 f'Indexes of the second list not found: {not_found_list_2}'))
