import pathlib
import unittest

from src.container import create_container
from src.models import AdminSistema, AdminEstacio, Estacionamento, Veiculo
from src.repo import EstacionamentoOthersRepo
from tests.factories import set_session, EstacionamentoFactory, VeiculoFactory
from tests.utils import get_adm_estacio, get_adm_sistema, make_engine, make_general_db_setup, make_savepoint, \
    general_db_teardown


class BaseTestEstacioOthers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[3] / 'test.ini')
        cls.container = create_container(config_path)

        conn_string = str(cls.container.config.get('db')['conn_string'])
        cls.engine = make_engine(conn_string)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.maxDiff = 3000
        self.crypto = self.container.crypto()

        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        set_session(self.session)  # Factories

        self.estacios = [EstacionamentoFactory.create(total_vaga=30, qtd_vaga_livre=10)]
        self.estacios.extend(EstacionamentoFactory.create_batch(10))
        self.veiculos = VeiculoFactory.create_batch(10)

        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(self.crypto, self.session)
        self.adm_estacio, self.adm_estacio_sess = get_adm_estacio(self.crypto, self.session)
        self.adm_estacio.estacionamento = self.estacios[0]
        self.adm_estacio.admin_mestre = False

        self.repo = EstacionamentoOthersRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        admin_estacio = self.session.query(AdminEstacio).all()
        estacios = self.session.query(Estacionamento).all()
        veiculos = self.session.query(Veiculo).all()

        self.assertEqual([self.adm_sis], admin_sis)
        self.assertIn(self.adm_estacio, admin_estacio)
        self.assertEqual(self.estacios, estacios)
        self.assertEqual(self.veiculos, veiculos)


if __name__ == '__main__':
    unittest.main()
