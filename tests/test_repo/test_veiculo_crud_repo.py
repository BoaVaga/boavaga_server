import pathlib
import unittest

from src.container import create_container
from src.models import Veiculo
from src.repo import VeiculoCrudRepo
from tests.factories import set_session, VeiculoFactory
from tests.utils import make_general_db_setup, general_db_teardown, make_engine, make_savepoint


class TestVeiculoCrudRepo(unittest.TestCase):
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

        self.veiculos = VeiculoFactory.create_batch(10)
        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.repo = VeiculoCrudRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

    def test_setup(self):
        veiculos = self.session.query(Veiculo).all()
        self.assertEqual(self.veiculos, veiculos)

    def test_get_ok(self):
        veiculo = self.veiculos[0]

        success, ret = self.repo.get(self.session, str(veiculo.id))

        self.assertEqual(True, success, f'Success should be True. Error: {ret}')
        self.assertEqual(veiculo, ret, 'Veiculos should match')

    def test_get_veiculo_not_found(self):
        for vid in [None, '   ', 'sadsad', '132444']:
            success, error = self.repo.get(self.session, vid)

            self.assertEqual('veiculo_nao_encontrado', error, f'Error should be "veiculo_nao_encontrado" on "{vid}"')
            self.assertEqual(False, success, f'Success should be False on "{vid}"')

    def test_list_ok(self):
        success, ret = self.repo.list(self.session)

        self.assertEqual(True, success, f'Success should be True. Error: {ret}')
        self.assertCountEqual(self.veiculos, ret, 'Veiculos should match')


if __name__ == '__main__':
    unittest.main()
