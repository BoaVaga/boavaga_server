import datetime
import pathlib
import unittest

from src.container import create_container
from src.models import AdminSistema, AdminEstacio, Estacionamento
from src.models.horario_divergente import HorarioDivergente
from src.repo import HorarioDivergenteRepo
from tests.factories import set_session, EstacionamentoFactory
from tests.factories.factory import HorarioDivergenteFactory
from tests.utils import make_engine, make_general_db_setup, make_savepoint, get_adm_sistema, get_adm_estacio, \
    general_db_teardown


class TestHorarioDivergenteRepo(unittest.TestCase):
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

        self.data, self.habre, self.hfecha = datetime.date.today(), datetime.time(13, 0, 0), datetime.time(20, 30, 0)

        self.estacios = EstacionamentoFactory.create_batch(10, cadastro_terminado=True)
        self.horarios = [HorarioDivergenteFactory.create(data=self.data, estacionamento=self.estacios[1])]

        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(self.crypto, self.session)
        self.adm_estacio, self.adm_estacio_sess = get_adm_estacio(self.crypto, self.session)
        self.adm_estacio.estacionamento = self.estacios[0]
        self.adm_estacio.admin_mestre = False

        self.adm_estacio_edit, self.adm_estacio_edit_sess = get_adm_estacio(self.crypto, self.session, n=6471)
        self.adm_estacio_edit.estacionamento = self.estacios[1]
        self.adm_estacio_edit.admin_mestre = False

        self.repo = HorarioDivergenteRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        admin_estacio = self.session.query(AdminEstacio).all()
        estacios = self.session.query(Estacionamento).all()
        horarios = self.session.query(HorarioDivergente).all()

        self.assertEqual([self.adm_sis], admin_sis)
        self.assertIn(self.adm_estacio, admin_estacio)
        self.assertEqual(self.estacios, estacios)
        self.assertEqual(self.horarios, horarios)

    def test_set_ok(self):
        success, horad = self.repo.set(self.adm_estacio_sess, self.session, self.data, self.habre, self.hfecha)

        self.assertEqual(True, success, f'Success should be True. Error: {horad}')
        self.assertEqual(self.data, horad.data, 'Data should match')
        self.assertEqual(self.habre, horad.hora_abr, 'Hora abre should match')
        self.assertEqual(self.hfecha, horad.hora_fec, 'Hora fecha should match')
        self.assertEqual(self.estacios[0], horad.estacionamento, 'Estacionamento should match')
        self.assertEqual(self.estacios[0].id, horad.estacio_fk, 'Estacio fk should match')

    def test_edit_ok(self):
        ori_id = self.horarios[0].id

        success, horad = self.repo.set(self.adm_estacio_edit_sess, self.session, self.data, self.habre, self.hfecha)

        self.assertEqual(True, success, f'Success should be True. Error: {horad}')
        self.assertEqual(self.data, horad.data, 'Data should match')
        self.assertEqual(self.habre, horad.hora_abr, 'Hora abre should match')
        self.assertEqual(self.hfecha, horad.hora_fec, 'Hora fecha should match')
        self.assertEqual(self.estacios[1], horad.estacionamento, 'Estacionamento should match')
        self.assertEqual(self.estacios[1].id, horad.estacio_fk, 'Estacio fk should match')
        self.assertEqual(ori_id, horad.id, 'Should not create a new instance')

    def test_set_no_permission(self):
        _sess = [self.adm_sis_sess, None]

        for i in range(len(_sess)):
            success, ret = self.repo.set(_sess[i], self.session, self.data, self.habre, self.hfecha)

            self.assertEqual('sem_permissao', ret, f'Error should be "sem_permissao" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_set_adm_estacio_no_estacio(self):
        adm_estacio, admin_estacio_sess = get_adm_estacio(self.crypto, self.session, n=9717)

        success, error = self.repo.set(admin_estacio_sess, self.session, self.data, self.habre, self.hfecha)

        self.assertEqual('sem_estacio', error, 'Error should be "sem_estacio"')
        self.assertEqual(False, success, 'Success should be False')

    def test_set_fecha_antes_abre(self):
        _TESTS = (
            (datetime.time(10, 30, 0), datetime.time(10, 29, 0)),
            (datetime.time(10, 30, 0), datetime.time(10, 30, 0)),
            (datetime.time(10, 30, 0), datetime.time(9, 31, 0))
        )

        for i in range(len(_TESTS)):
            abr, fec = _TESTS[i]
            success, error = self.repo.set(self.adm_estacio_sess, self.session, self.data, abr, fec)
            
            self.assertEqual('fecha_antes_de_abrir', error, 
                             f'Error should be "fecha_antes_de_abrir" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_set_data_passada(self):
        datas = [datetime.date(2021, 10, 30), datetime.date(2020, 12, 30), datetime.date(2021, 11, 15)]

        for data in datas:
            success, error = self.repo.set(self.adm_estacio_sess, self.session, data, self.habre, self.hfecha)

            self.assertEqual('data_passada', error, f'Error should be "data_passada" on {data}')
            self.assertEqual(False, success, f'Success should be False on {data}')

    def test_delete_ok(self):
        ori_id = int(self.horarios[0].id)
        success, error = self.repo.delete(self.adm_estacio_edit_sess, self.session, self.data)

        self.assertIsNone(error, 'Error should be None')
        self.assertEqual(True, success, 'Success should be True')

        instance = self.session.query(HorarioDivergente).get(ori_id)
        self.assertIsNone(instance, 'Should delete the instance from the db')

    def test_delete_sem_permissao(self):
        _sess = [self.adm_sis_sess, None]

        for i in range(len(_sess)):
            success, ret = self.repo.delete(_sess[i], self.session, self.data)

            self.assertEqual('sem_permissao', ret, f'Error should be "sem_permissao" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_delete_sem_estacio(self):
        adm_estacio, admin_estacio_sess = get_adm_estacio(self.crypto, self.session, n=9717)

        success, error = self.repo.delete(admin_estacio_sess, self.session, self.data)

        self.assertEqual('sem_estacio', error, 'Error should be "sem_estacio"')
        self.assertEqual(False, success, 'Success should be False')

    def test_delete_data_nao_encontrada(self):
        data = datetime.date(2021, 11, 10)

        success, error = self.repo.delete(self.adm_estacio_edit_sess, self.session, data)
        self.assertEqual('data_nao_encontrada', error, 'Error should be "data_nao_encontrada"')
        self.assertEqual(False, success, 'Success should be False')


if __name__ == '__main__':
    unittest.main()
