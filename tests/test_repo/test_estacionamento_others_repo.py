import pathlib
import unittest

from src.container import create_container
from src.models import AdminSistema, AdminEstacio, Estacionamento, Veiculo
from src.repo import EstacionamentoOthersRepo
from tests.factories import set_session, EstacionamentoFactory, VeiculoFactory
from tests.utils import get_adm_estacio, get_adm_sistema, make_engine, make_general_db_setup, make_savepoint, \
    general_db_teardown


class TestEstacionamentoOthersRepo(unittest.TestCase):
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
        self.adm_estacio.admin_mestre = True

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

    def test_att_vagas_ok(self):
        estacio_id = self.adm_estacio.estacionamento.id

        for n in (0, 1, 20, 29, 30):
            success, ret = self.repo.atualizar_vagas_livres(self.adm_estacio_sess, self.session, n)

            self.assertIsNone(ret, f'Should not return anything on {n}')
            self.assertEqual(True, success, f'Success should be True on {n}')

            estacio = self.session.query(Estacionamento).get(estacio_id)
            self.assertEqual(n, estacio.qtd_vaga_livre, f'Should update the amount of vaga livre on {n}')
            self.assertEqual(30, estacio.total_vaga, f'Total vaga should keep the same on {n}')

    def test_att_vagas_amount_negative(self):
        estacio_id = self.adm_estacio.estacionamento.id

        for n in (-1, -30, -40):
            success, ret = self.repo.atualizar_vagas_livres(self.adm_estacio_sess, self.session, n)

            self.assertEqual('quantia_negativa', ret, f'Error should be "quantia_negativa" on {n}')
            self.assertEqual(False, success, f'Success should be False on {n}')

            estacio = self.session.query(Estacionamento).get(estacio_id)
            self.assertEqual(10, estacio.qtd_vaga_livre, f'Should keep the amount of vaga livre on {n}')
            self.assertEqual(30, estacio.total_vaga, f'Total vaga should keep the same on {n}')

    def test_att_vagas_amount_bigger_than_max(self):
        estacio_id = self.adm_estacio.estacionamento.id

        success, ret = self.repo.atualizar_vagas_livres(self.adm_estacio_sess, self.session, 31)

        self.assertEqual('quantia_maior_que_total', ret, 'Error should be "quantia_maior_que_total"')
        self.assertEqual(False, success, f'Success should be False')

        estacio = self.session.query(Estacionamento).get(estacio_id)
        self.assertEqual(10, estacio.qtd_vaga_livre, 'Should keep the amount of vaga livre')
        self.assertEqual(30, estacio.total_vaga, 'Total vaga should keep the same')

    def test_att_vagas_adm_estacio_with_no_estacio(self):
        self.adm_estacio.estacionamento = None

        success, ret = self.repo.atualizar_vagas_livres(self.adm_estacio_sess, self.session, 10)

        self.assertEqual('sem_estacionamento', ret, 'Error should be "sem_estacionamento"')
        self.assertEqual(False, success, 'Success should be False')

    def test_att_vagas_adm_sistema(self):
        success, ret = self.repo.atualizar_vagas_livres(self.adm_sis_sess, self.session, 10)

        self.assertEqual('sem_estacionamento', ret, 'Error should be "sem_estacionamento"')
        self.assertEqual(False, success, 'Success should be False')

    def test_att_vagas_not_logged_in(self):
        success, ret = self.repo.atualizar_vagas_livres(None, self.session, 10)

        self.assertEqual('sem_permissao', ret, 'Error should be "sem_permissao"')
        self.assertEqual(False, success, 'Success should be False')


if __name__ == '__main__':
    unittest.main()
