import logging
import pathlib
import unittest

from src.classes import Point
from src.container import create_container
from src.models import AdminSistema, AdminEstacio, PedidoCadastro, Endereco, Estacionamento, HorarioPadrao
from src.repo import PedidoCadastroAprovacaoRepo
from tests.factories import PedidoCadastroFactory, set_session, EnderecoFactory
from tests.utils import general_db_teardown, make_savepoint, get_adm_sistema, get_adm_estacio, make_general_db_setup, \
    make_engine


class TestPedidoCadastroAprovacaoRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logging.basicConfig(level=logging.FATAL)

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

        self.crypto = self.container.crypto()

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(self.crypto, self.session)
        self.adm_estacio, self.adm_estacio_sess = get_adm_estacio(self.crypto, self.session)

        self.pedidos = PedidoCadastroFactory.create_batch(10)
        self.pedidos.append(PedidoCadastroFactory.create(num_rejeicoes=2))

        self.session.commit()
        make_savepoint(self.conn, self.session)

        self.repo = PedidoCadastroAprovacaoRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        admin_estacio = self.session.query(AdminEstacio).all()
        pedidos = self.session.query(PedidoCadastro).all()

        self.assertEqual([self.adm_sis], admin_sis)
        self.assertIn(self.adm_estacio, admin_estacio)
        self.assertEqual(self.pedidos, pedidos)

    def test_accept_ok(self):
        pedido: PedidoCadastro = self.pedidos[0]
        pedido_id = str(pedido.id)
        adm_estacio: AdminEstacio = pedido.admin_estacio

        cord = Point(x='30.475', y='-78.314')
        empty_hora_p = HorarioPadrao()

        endereco_copy = Endereco.from_dict(pedido.endereco.to_dict())
        endereco_copy.coordenadas = cord

        success, estacio = self.repo.accept(self.adm_sis_sess, self.session, pedido_id, cord)

        self.assertEqual(True, success, f'Success should be True. Error: {estacio}')

        self.assertIsNotNone(estacio.id, 'ID should not be null')
        self.assertEqual(pedido.nome, estacio.nome, 'Nomes should match')
        self.assertEqual(pedido.telefone, estacio.telefone, 'Telefones should match')
        self.assertEqual(endereco_copy, estacio.endereco, 'Enderecos should match')
        self.assertEqual(pedido.foto, estacio.foto, 'Fotos should match')

        self.assertEqual(False, estacio.esta_suspenso, 'Esta suspenso should be False')
        self.assertEqual(False, estacio.esta_aberto, 'Esta aberto should be False')
        self.assertEqual(False, estacio.cadastro_terminado, 'Cadastro terminado should be True')
        self.assertEqual(0, estacio.qtd_vaga_livre, 'Qtd vaga livre should start as 0')
        self.assertEqual(0, estacio.total_vaga, 'Total vaga should start as 0')

        empty_hora_p.id = estacio.horap_fk
        self.assertEqual(empty_hora_p, estacio.horario_padrao, 'Horario padrao should be empty')

        self.assertEqual(pedido.endereco_fk, estacio.endereco_fk, 'Endereco foreign keys should match')
        self.assertEqual(pedido.foto_fk, estacio.foto_fk, 'Foto foreign keys should match')

        self.assertEqual(True, adm_estacio.admin_mestre, 'Admin estacio should be master')
        self.assertEqual(estacio.id, adm_estacio.estacio_fk, 'Admin estacio foreign key should match estacio id')

        db_estacio = self.session.query(Estacionamento).get(estacio.id)
        self.assertEqual(estacio, db_estacio, 'Estacionamentos should match on db level')

        db_pedido = self.session.query(PedidoCadastro).get(pedido_id)
        self.assertIsNone(db_pedido, 'The Pedido should be deleted from the database')

        db_adm_estacio = self.session.query(AdminEstacio).get(adm_estacio.id)
        self.assertEqual(adm_estacio, db_adm_estacio, 'Admins estacio should match on db level')

    def test_accept_ok_no_foto(self):
        self.pedidos[0].foto_fk = self.pedidos[0].foto = None

        self.test_accept_ok()

    def test_accept_no_permission(self):
        _sessions = [self.adm_estacio_sess, None]
        for i in range(len(_sessions)):
            success, error = self.repo.accept(_sessions[i], self.session, str(self.pedidos[0].id), Point(1, 1))

            self.assertEqual('sem_permissao', error, f'Error should be "sem_permissao" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_accept_pedido_not_found(self):
        for p_id in ['', '-123', '59841']:
            success, error = self.repo.accept(self.adm_sis_sess, self.session, p_id, Point(1, 1))

            self.assertEqual('pedido_nao_encontrado', error, f'Error should be "pedido_nao_encontrado" for id {p_id}')
            self.assertEqual(False, success, f'Success should be False for id {p_id}')

    def test_reject_ok(self):
        pedido: PedidoCadastro = self.pedidos[0]
        pedido_id = str(pedido.id)
        msg = 'Sla, estou com pregui??a de pensar em algo, ent??o vai s?? isso mesmo e j?? era :)'

        success, error = self.repo.reject(self.adm_sis_sess, self.session, pedido_id, msg)
        self.assertEqual(True, success, f'Success should be True. Error: {error}')
        self.assertIsNone(error, 'Error should be None')

        self.assertEqual(1, pedido.num_rejeicoes, 'Num rejeicoes should increase')
        self.assertEqual(msg, pedido.msg_rejeicao, 'Should set the msg rejeicao')

        db_pedido = self.session.query(PedidoCadastro).get(pedido_id)
        self.assertEqual(pedido, db_pedido, 'Pedidos should match on db level')

    def test_reject_ok_2(self):
        pedido: PedidoCadastro = self.pedidos[-1]
        pedido_id = str(pedido.id)
        msg = '    Sla, estou com pregui??a de pensar em algo, ent??o vai s?? isso mesmo e j?? era :)    '

        success, error = self.repo.reject(self.adm_sis_sess, self.session, pedido_id, msg)
        self.assertEqual(True, success, f'Success should be True. Error: {error}')
        self.assertIsNone(error, 'Error should be None')

        self.assertEqual(3, pedido.num_rejeicoes, 'Num rejeicoes should increase')
        self.assertEqual(msg.strip(), pedido.msg_rejeicao, 'Should set the msg rejeicao')

        db_pedido = self.session.query(PedidoCadastro).get(pedido_id)
        self.assertEqual(pedido, db_pedido, 'Pedidos should match on db level')

    def test_reject_no_permission(self):
        _sessions = [self.adm_estacio_sess, None]
        for i in range(len(_sessions)):
            success, error = self.repo.reject(_sessions[i], self.session, str(self.pedidos[0].id), 'Qualquer coisa')

            self.assertEqual('sem_permissao', error, f'Error should be "sem_permissao" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')

    def test_reject_pedido_not_found(self):
        for p_id in ['', '-123', '59841']:
            success, error = self.repo.reject(self.adm_sis_sess, self.session, p_id, 'Qualquer coisa')

            self.assertEqual('pedido_nao_encontrado', error, f'Error should be "pedido_nao_encontrado" for id {p_id}')
            self.assertEqual(False, success, f'Success should be False for id {p_id}')


if __name__ == '__main__':
    unittest.main()
