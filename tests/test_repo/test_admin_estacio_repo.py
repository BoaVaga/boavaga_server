import pathlib
import unittest

from src.container import create_container
from src.enums import UserType
from src.models import AdminEstacio, Estacionamento
from src.classes import UserSession
from src.repo import AdminEstacioRepo
from src.services import Crypto
from tests.factories import set_session, AdminEstacioFactory, EstacionamentoFactory
from tests.utils import make_general_db_setup, general_db_teardown, make_engine, make_savepoint, get_adm_sistema, \
    get_adm_estacio


class TestAdminEstacioRepo(unittest.TestCase):
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

        self.crypto = Crypto(is_testing=True, salt_rounds=12)
        senha = self.crypto.hash_password(b'outraSenha')

        self.estacios = EstacionamentoFactory.create_batch(5)

        self.admin_estacio = AdminEstacioFactory.create_batch(10)
        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(self.crypto, self.session)
        a, self.valid_user_sess = get_adm_estacio(self.crypto, self.session)
        a.estacionamento = self.estacios[0]
        a.admin_mestre = True

        b, self.not_master_user_sess = get_adm_estacio(self.crypto, self.session, n=5742)
        b.estacionamento = self.estacios[1]
        b.admin_mestre = False

        c, self.invalid_user_sess = get_adm_estacio(self.crypto, self.session, n=5743)

        self.admin_estacio.extend([a, b, c])

        self.repo = AdminEstacioRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

    def test_setup(self):
        admin_estacio = self.session.query(AdminEstacio).all()
        estacios = self.session.query(Estacionamento).all()

        self.assertEqual(self.admin_estacio, admin_estacio)
        self.assertEqual(self.estacios, estacios)

    def test_create_ok(self):
        requests = [
            ('jorge12@email.com', 'matheus12'),
            ('joaquim@email.com', 'joaquim12'),
            ('fernanda@email.com', 'fernanda12'),
            ('mariana@email.com', 'mariana12'),
        ]

        for i in range(len(requests)):
            email, senha = requests[i]

            success, error_or_admin = self.repo.create_admin(self.session, email, senha)
            self.assertEqual(True, success, f'Success should be True on {i}. Error: {error_or_admin}')
            self.assertIsNotNone(error_or_admin, f'Admin should not be null on {i}')

            self.assertEqual(email, error_or_admin.email, f'Email does not match on {i}')
            self.assertEqual(True, self.crypto.check_password(senha.encode('utf8'), error_or_admin.senha),
                             f'Senha does not match on {i}')

            self.assertEqual(False, error_or_admin.admin_mestre, f'Admin mestre should be False on {i}')

    def test_create_email_already_exists(self):
        requests = [
            (self.admin_estacio[0].email, 'senha123'),
        ]

        for i in range(len(requests)):
            email, senha = requests[i]

            success, error = self.repo.create_admin(self.session, email, senha)

            self.assertEqual('email_ja_cadastrado', error, f'Error should be "email_ja_cadastrado" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_add_to_estacio_ok(self):
        expect_estacio_id = int(self.estacios[0].id)

        for i in range(5):
            adm = self.admin_estacio[i]

            success, error = self.repo.add_to_estacio(self.valid_user_sess, self.session, adm.email)
            self.assertEqual(True, success, f'Success should be True on {i}. Error: {error}')
            self.assertIsNone(error, f'Error should be null on {i}')

            self.assertEqual(expect_estacio_id, adm.estacio_fk, f'Estacio fk should match on {i}')
            self.assertEqual(False, adm.admin_mestre, f'Admin mestre should be False on {i}')

    def test_add_invalid_permission(self):
        email = 'jorge12@email.com'

        sessions = [self.not_master_user_sess, self.invalid_user_sess, UserSession(UserType.SISTEMA, 1), None]
        for i in range(len(sessions)):
            success, error = self.repo.add_to_estacio(sessions[i], self.session, email)

            self.assertEqual('sem_permissao', error, f'Error should be "sem_permissao" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_add_email_not_found(self):
        success, error = self.repo.add_to_estacio(self.valid_user_sess, self.session, 'asdjhasdu@adaszds')

        self.assertEqual('email_not_found', error, f'Error should be "email_not_found"')
        self.assertEqual(False, success, 'Success should be False')

    def test_add_adm_already_assigned(self):
        email = self.admin_estacio[-2].email
        success, error = self.repo.add_to_estacio(self.valid_user_sess, self.session, email)

        self.assertEqual('admin_already_assigned', error, 'Error should be "admin_already_assigned"')
        self.assertEqual(False, success, 'Success should be False')

    def _check_response(self, response, i):
        self.assertEqual(200, response.status_code, 'Should return a 200 OK code')
        self.assertIn('data', response.json, f'JSON should contain "data" on {i}')
        self.assertIn('login', response.json['data'], f'Base data should contain "login" on {i}')

        return response.json['data']['login']


if __name__ == '__main__':
    unittest.main()
