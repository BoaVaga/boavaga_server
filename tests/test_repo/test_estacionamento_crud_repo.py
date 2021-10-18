import datetime
import pathlib
import unittest
from decimal import Decimal

from src.container import create_container
from src.enums import UserType
from src.models import AdminSistema, AdminEstacio, Estacionamento, Veiculo, ValorHora
from src.repo import EstacionamentoCrudRepo
from tests.factories import set_session, HorarioPadraoFactory, EstacionamentoFactory, VeiculoFactory, \
    ValorHoraInputFactory
from tests.utils import make_engine, make_general_db_setup, make_savepoint, get_adm_sistema, get_adm_estacio, \
    general_db_teardown

_DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')

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

    def _general_test_create_ok(self, adm_sess, estacio='def', horario_padrao='def', total_vaga='def', descricao='def',
                                valores_hora='def'):
        estacio = self.estacios[0] if estacio == 'def' else estacio
        estacio_id = None if adm_sess.tipo == UserType.ESTACIONAMENTO else estacio.id
        horario_padrao = HorarioPadraoFactory.build() if horario_padrao == 'def' else horario_padrao
        total_vaga = 20 if total_vaga == 'def' else total_vaga
        descricao = 'Abobrinha com limão' if descricao == 'def' else descricao
        if valores_hora == 'def':
            valores_hora = []
            for i in range(4):
                valores_hora.append(ValorHoraInputFactory.create(veiculo_id=str(self.veiculos[i].id)))

        if valores_hora is not None:
            expect_valores_hora = [
                ValorHora(estacio_fk=estacio.id, veiculo_fk=int(v.veiculo_id), valor=v.valor) for v in valores_hora
            ]
        else:
            expect_valores_hora = []

        v_list = ('id', 'nome', 'telefone', 'endereco_fk', 'foto_fk')
        to_keep = {k: getattr(estacio, k) for k in v_list}

        ok, ret = self.repo.create(adm_sess, self.session, total_vaga, horario_padrao,
                                   descricao=descricao, valores_hora=valores_hora, estacio_id=estacio_id)

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

    def test_create_with_adm_estacio_ok(self):
        self._general_test_create_ok(self.adm_estacio_sess)

    def test_create_with_adm_sistema_ok(self):
        self._general_test_create_ok(self.adm_sis_sess)

    def test_create_hora_padrao_vazio_ok(self):
        _kw = {}
        for dia in _DIAS:
            for tipo in ['abr', 'fec']:
                _kw['_'.join((dia, tipo))] = None

        self._general_test_create_ok(self.adm_estacio_sess, horario_padrao=HorarioPadraoFactory.build(**_kw))

    def test_create_total_vaga_1_ok(self):
        self._general_test_create_ok(self.adm_estacio_sess, total_vaga=1)

    def test_create_descricao_quase_limite(self):
        self._general_test_create_ok(self.adm_estacio_sess, descricao='Á'*2000)

    def test_create_descricao_vazia(self):
        self._general_test_create_ok(self.adm_estacio_sess, descricao=None)

    def test_create_valores_hora_vazio(self):
        self._general_test_create_ok(self.adm_estacio_sess, valores_hora=None)

    def test_create_fail_total_vaga_invalid(self):
        for t_vaga in [0, -1, -1234]:
            ok, ret = self.repo.create(self.adm_estacio_sess, self.session, t_vaga, HorarioPadraoFactory.build())

            self.assertEqual('total_vaga_nao_positivo', ret, f'Error should be "total_vaga_nao_positivo" on {t_vaga}')
            self.assertEqual(False, ok, f'Success should be False on {t_vaga}')

    def test_create_fail_hora_padrao_fecha_antes_abrir(self):
        antes = datetime.time(12, 30)
        _default_kw = {}
        for dia in _DIAS:
            for tipo in ['abr', 'fec']:
                _default_kw['_'.join((dia, tipo))] = None

        for caso, depois in (('menor', datetime.time(12, 29)), ('igual', datetime.time(12, 30))):
            for dia in ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']:
                _kw = dict(_default_kw)
                _kw.update({f'{dia}_abr': antes, f'{dia}_fec': depois})
                hora_p = HorarioPadraoFactory.build(**_kw)

                ok, ret = self.repo.create(self.adm_estacio_sess, self.session, 5, hora_p)

                self.assertEqual('hora_padrao_fecha_antes_de_abrir',
                                 ret, f'Error should be "hora_padrao_fecha_antes_de_abrir" on "{dia}:{caso}"')
                self.assertEqual(False, ok, f'Success should be False on "{dia}:{caso}"')

    def test_create_fail_hora_padrao_apenas_abre_ou_fecha(self):
        _default_kw = {}
        for dia in _DIAS:
            for tipo in ['abr', 'fec']:
                _default_kw['_'.join((dia, tipo))] = None

        hora = datetime.time(12, 30)
        for dia in ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']:
            for attr_hora, attr_none in [('abr', 'fec'), ('fec', 'abr')]:
                _kw = dict(_default_kw)
                _kw.update({f'{dia}_{attr_hora}': hora, f'{dia}_{attr_none}': None})
                hora_p = HorarioPadraoFactory.build(**_kw)

                ok, ret = self.repo.create(self.adm_estacio_sess, self.session, 5, hora_p)

                self.assertEqual('hora_padrao_dia_incompleto',
                                 ret, f'Error should be "hora_padrao_dia_incompleto" on "{dia}:{attr_none}"')
                self.assertEqual(False, ok, f'Success should be False on "{dia}:{attr_none}"')

    def test_create_fail_descricao_muito_grande(self):
        d = 'A' * 2001

        ok, ret = self.repo.create(self.adm_estacio_sess, self.session, 5, HorarioPadraoFactory.build(), descricao=d)
        self.assertEqual('descricao_muito_grande', ret, 'Error should be "descricao_muito_grande"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_create_fail_valor_hora_preco_invalido(self):
        for preco in ['0', '0.00', '-1', '-1234.535']:
            valores = [ValorHoraInputFactory.build(valor=Decimal(preco), veiculo_id=str(self.estacios[0].id))]

            ok, ret = self.repo.create(self.adm_estacio_sess, self.session, 5, HorarioPadraoFactory.build(),
                                       valores_hora=valores)

            self.assertEqual('valor_hora_preco_nao_positivo', ret, f'Error should be "valor_hora_preco_nao_positivo" on {preco}')
            self.assertEqual(False, ok, f'Success should be False on {preco}')

    def test_create_fail_valor_hora_veiculo_nao_encontrado(self):
        veiculo_id = str(self.veiculos[-1].id)
        self.session.delete(self.veiculos[-1])

        valores = [ValorHoraInputFactory.build(valor=Decimal('15.5'), veiculo_id=veiculo_id)]
        ok, ret = self.repo.create(self.adm_estacio_sess, self.session, 5, HorarioPadraoFactory.build(),
                                   valores_hora=valores)

        self.assertEqual('valor_hora_veiculo_nao_encontrado', ret, 'Error should be "valor_hora_veiculo_nao_encontrado"')
        self.assertEqual(False, ok, 'Success should be False')


if __name__ == '__main__':
    unittest.main()
