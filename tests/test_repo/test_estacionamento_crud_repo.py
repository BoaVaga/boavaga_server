import pathlib
import unittest

from src.container import create_container
from src.models import AdminSistema, AdminEstacio, Estacionamento, Veiculo, ValorHora
from src.repo import EstacionamentoCrudRepo
from tests.factories import set_session, HorarioPadraoFactory, EstacionamentoFactory, VeiculoFactory, \
    ValorHoraInputFactory
from tests.utils import make_engine, make_general_db_setup, make_savepoint, get_adm_sistema, get_adm_estacio, \
    general_db_teardown


class TestEstacionamentoCrudRepo(unittest.TestCase):
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

        self.estacios = EstacionamentoFactory.create_batch(10)
        self.veiculos = VeiculoFactory.create_batch(10)

        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(self.crypto, self.session)
        self.adm_estacio, self.adm_estacio_sess = get_adm_estacio(self.crypto, self.session)
        self.adm_estacio.estacionamento = self.estacios[0]
        self.adm_estacio.admin_mestre = True

        self.repo = EstacionamentoCrudRepo()

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

    def test_create_adm_estacio_ok(self):
        estacio = self.estacios[0]
        horario_padrao = HorarioPadraoFactory.build()
        total_vaga = 20
        descricao = None
        valores_hora = ValorHoraInputFactory.create_batch(4)
        expect_valores_hora = [
            ValorHora(estacio_fk=estacio.id, veiculo_fk=int(v.veiculo_id), valor=v.valor) for v in valores_hora
        ]

        v_list = ('id', 'nome', 'telefone', 'endereco_fk', 'foto_fk')
        to_keep = {k: getattr(estacio, k) for k in v_list}

        ok, ret = self.repo.create(self.adm_estacio_sess, self.session, total_vaga, horario_padrao,
                                   descricao=descricao, valores_hora=valores_hora)

        self.assertEqual(True, ok, f'Success should be True. Error: {ret}')
        for k, v in to_keep.items():
            self.assertEqual(v, getattr(ret, k), f'{k} should match')

        self.assertEqual(False, ret.esta_suspenso, 'Esta suspenso should be False')
        self.assertEqual(True, ret.esta_aberto, 'Esta aberto should be True')
        self.assertEqual(True, ret.cadastro_terminado, 'Cadastro terminado should be True')
        self.assertEqual(total_vaga, ret.total_vaga, 'Total vaga should match')
        self.assertEqual(total_vaga, ret.qtd_vaga_livre, 'Qtd vaga livre should be maximum')
        self.assertEqual(descricao, ret.descricao, 'Descricao should match')
        self.assertEqual(horario_padrao, ret.horario_padrao, 'Horario padrao should match')

        copy_v_hora = [ValorHora(estacio_fk=v.estacio_fk, veiculo_fk=v.veiculo_fk, valor=v.valor) for v in ret.valores_hora]
        self.assertCountEqual(expect_valores_hora, copy_v_hora, 'Valores hora should match')

        self.assertEqual(0, len(ret.horas_divergentes), 'Horas divergentes should be empty')

        db_estacio = self.session.query(Estacionamento).get(estacio.id)
        self.assertEqual(estacio, db_estacio, 'Estacios should match on db level')


if __name__ == '__main__':
    unittest.main()
