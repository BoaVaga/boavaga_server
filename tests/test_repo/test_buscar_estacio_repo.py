import pathlib
import random
import unittest

from src.classes import Point
from src.container import create_container
from src.models import Endereco, Estacionamento
from src.repo import BuscarEstacioRepo
from tests.factories import set_session, EnderecoFactory, EstacionamentoFactory
from tests.utils import make_general_db_setup, make_engine, make_savepoint, general_db_teardown


class TestBuscarEstacioRepo(unittest.TestCase):
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
        cfg = self.container.config.get('busca_estacio')
        self.distance = int(cfg['distancia'])
        self.raio_terra = int(cfg['raio_terra'])

        self.maxDiff = 1000
        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        set_session(self.session)  # Factories

        self.center = Point('-23.4936088353667', '-46.70926089220919')
        self.ordered_coords = [Point('-23.502021', '-46.708661'), Point('-23.493971', '-46.661464'),
                               Point('-23.496181', '-46.610568'), Point('-23.294186', '-45.927184')]
        _rnd_indexes = list(range(len(self.ordered_coords)))
        random.shuffle(_rnd_indexes)

        self.coords_order_map = {_rnd_indexes[i]: i for i in range(len(_rnd_indexes))}
        self.not_ordered_coords = [self.ordered_coords[i] for i in _rnd_indexes]

        self.enderecos = [EnderecoFactory.create(coordenadas=c) for c in self.not_ordered_coords]
        self.estacios = [EstacionamentoFactory.create(endereco=e) for e in self.enderecos]

        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.repo = BuscarEstacioRepo(self.distance)

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

    def test_setup(self):
        enderecos = self.session.query(Endereco).all()
        estacios = self.session.query(Estacionamento).all()

        self.assertEqual(self.enderecos, enderecos)
        self.assertEqual(self.estacios, estacios)

    def test_busca_ok(self):
        expect_ends_id = [self.enderecos[self.coords_order_map[i]].id for i in range(3)]
        expect_estacios = self.session.query(Estacionamento).filter(Estacionamento.endereco_fk.in_(expect_ends_id)).all()
        success, ret = self.repo.buscar(self.session, self.center)

        self.assertEqual(True, success, f'Success should be True. Error: {ret}')

        list_ret = list(ret)
        self.assertCountEqual(expect_estacios, list_ret, 'List of estacios should match')
        self.assertListEqual(expect_estacios, list_ret, 'Order of estacios should match')


if __name__ == '__main__':
    unittest.main()
