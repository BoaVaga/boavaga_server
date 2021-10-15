import logging
import pathlib
import unittest
from unittest.mock import Mock, ANY

from dependency_injector.providers import Singleton
from sgqlc.operation import Operation

from src.app import create_app
from src.classes import Point
from src.container import create_container
from src.models import Endereco, HorarioDivergente, HorarioPadrao, ValorHora, Estacionamento
from src.repo.repo_container import create_repo_container
from tests.factories.factory import EstacionamentoFactory
from tests.test_api.nodes import Mutation
from tests.utils import general_db_teardown, make_savepoint, get_adm_sistema_login, make_general_db_setup, \
    make_mocked_cached_provider, make_engine, convert_dct_snake_case


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
        self.maxDiff = 3000
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
        self.container.cached().close()

    def test_setup(self):
        self.assertEqual(True, self.login_success, f'Success should be True. Error: {self.login_token}')
        self.assertIsNotNone(self.login_token, 'Login token should not be null')

    def test_accept_ok(self):
        pedido_id, coord = '123', Point('5.7', '-90.3')
        estacio = EstacionamentoFactory.build(valores_hora=3, horas_divergentes=4)
        estacio.endereco.coordenadas = coord

        self.repo.accept.return_value = (True, estacio)

        mutation = Operation(Mutation)
        mutation.accept_pedido_cadastro(pedido_id=pedido_id, coordenadas=coord)

        response = self.client.post('/graphql', json={'query': mutation.__to_graphql__(auto_select_depth=5)})
        data = self._check_response(response, 'acceptPedidoCadastro')

        self.assertIsNone(data['error'], 'Error should be null')
        self.assertEqual(True, data['success'], 'Success should be True')

        self.repo.accept.assert_called_once_with(self.user_sess, ANY, pedido_id, coord)

        self._check_estacio(estacio, data['estacionamento'], 'Estacionamentos should match')

    def test_accept_error(self):
        pedido_id, coord = '123', Point('5.7', '-90.3')

        for error in ['sem_permissao', 'pedido_nao_encontrado', None]:
            self.repo.accept.reset_mock()
            if error is None:
                self.repo.accept.side_effect = Exception('Random Error')
                error = 'erro_desconhecido'
            else:
                self.repo.accept.return_value = (False, error)

            mutation = Operation(Mutation)
            mutation.accept_pedido_cadastro(pedido_id=pedido_id, coordenadas=coord)

            response = self.client.post('/graphql', json={'query': mutation.__to_graphql__(auto_select_depth=5)})
            data = self._check_response(response, 'acceptPedidoCadastro')

            self.assertEqual(error, data['error'], f'Error should be "{error}"')
            self.assertEqual(False, data['success'], f'Success should be False on "{error}"')
            self.assertIsNone(data['estacionamento'], f'Estacionamento should be None on "{error}"')

    def _check_response(self, response, group, i=0):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn(group, response.json['data'], f'Base data should contain "{group}" on {i}')

        return response.json['data'][group]

    def _check_estacio(self, estacio: Estacionamento, ret, msg):
        dct = convert_dct_snake_case(ret)
        dct['id'] = int(dct['id'])

        endereco, horas_divergentes, hora_padrao, valores_hora = None, None, None, None

        if 'endereco' in dct:
            endereco = Endereco.from_dict(dct['endereco'])
            dct['endereco_fk'] = endereco.id
        if 'horas_divergentes' in dct:
            horas_divergentes = [HorarioDivergente.from_dict(convert_dct_snake_case(d)) for d in dct['horas_divergentes']]
        if 'horario_padrao' in dct:
            hora_padrao = HorarioPadrao.from_dict(convert_dct_snake_case(dct['horario_padrao']))
        if 'valores_hora' in dct:
            valores_hora = [ValorHora.from_dict(d) for d in dct['valores_hora']]

        estacio.foto_fk = estacio.horap_fk = estacio.horario_padrao.id = None
        foto_str = str(estacio.foto)

        for v_hora in estacio.valores_hora:
            v_hora.veiculo.id = v_hora.veiculo_fk = v_hora.estacio_fk = None
        for hora_d in estacio.horas_divergentes:
            hora_d.estacio_fk = None

        _kwargs = {k: v for k, v in dct.items() if k not in ('endereco', 'horas_divergentes', 'horario_padrao', 'valores_hora')}
        _est = Estacionamento(**_kwargs)

        self.assertEqual(estacio, _est, msg)
        self.assertEqual(foto_str, dct['foto'], msg)
        self.assertEqual(estacio.endereco, endereco, msg)
        self.assertCountEqual(estacio.horas_divergentes, horas_divergentes, msg)
        self.assertEqual(estacio.horario_padrao, hora_padrao, msg)
        self.assertEqual(estacio.valores_hora, valores_hora, msg)


if __name__ == '__main__':
    unittest.main()
