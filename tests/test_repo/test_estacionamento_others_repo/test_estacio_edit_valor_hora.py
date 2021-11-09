from decimal import Decimal
from src.models.estacionamento import Estacionamento
from src.models.valor_hora import ValorHora
from tests.factories.factory import ValorHoraFactory
from tests.test_repo.test_estacionamento_others_repo.base import BaseTestEstacioOthers

class TestEstacioEditValorHora(BaseTestEstacioOthers):
    def _test_general_edit_ok(self, user_sess, veiculo='def', estacio_id='def', expec_estacio_id='def'):
        veiculo = self.veiculos[0] if veiculo == 'def' else veiculo
        v_id = str(veiculo.id)
        valor = Decimal('15.20')

        expect_estacio_id = self.adm_estacio.estacio_fk if expec_estacio_id == 'def' else expec_estacio_id
        estacio_id = None if estacio_id == 'def' else estacio_id

        success, valor_hora = self.repo.edit_valor_hora(user_sess, self.session, v_id, valor, estacio_id=estacio_id)
        self.assertEqual(True, success, f'Sucess should be True. Error: {valor_hora}')
        self.assertEqual(veiculo, valor_hora.veiculo, 'Veiculos should match')
        self.assertEqual(valor, valor_hora.valor, 'Valor should match')
        self.assertEqual(expect_estacio_id, valor_hora.estacio_fk, 'Estacio fk should match')

    def test_edit_valor_hora_ok(self):
        self._test_general_edit_ok(self.adm_estacio_sess)

    def test_edit_valor_hora_ok_adm_sis(self):
        self._test_general_edit_ok(self.adm_sis_sess, estacio_id=str(self.estacios[1].id))

    def test_edit_valor_hora_sem_permissao(self):
        success, error = self.repo.edit_valor_hora(None, self.session, str(self.veiculos[0].id), Decimal(1))

        self.assertEqual('sem_permissao', error, 'Error should be "sem_permissao"')
        self.assertEqual(False, success, 'Success should be False')

    def test_edit_valor_hora_estacio_not_found(self):
        for eid in [None, '-1', 'asd4165454']:
            success, error = self.repo.edit_valor_hora(self.adm_sis_sess, self.session, str(self.veiculos[0].id),
                                                       Decimal(1), estacio_id=eid)

            self.assertEqual('estacio_nao_encontrado', error, 'Error should be "estacio_nao_encontrado"')
            self.assertEqual(False, success, 'Success should be False')

    def test_edit_valor_hora_ignorar_estacio_id_com_adm_estacio(self):
        expec_e_id = self.adm_estacio.estacio_fk
        e_id = str(self.estacios[1].id)

        self._test_general_edit_ok(self.adm_estacio_sess, estacio_id=e_id, expec_estacio_id=expec_e_id)

    def test_edit_valor_hora_veiculo_not_found(self):
        for vid in [None, '-1', 'asd4165454']:
            success, error = self.repo.edit_valor_hora(self.adm_estacio_sess, self.session, vid, Decimal(1))

            self.assertEqual('veiculo_nao_encontrado', error, 'Error should be "veiculo_nao_encontrado"')
            self.assertEqual(False, success, 'Success should be False')

    def test_edit_valor_hora_check_not_adding(self):
        estacio: Estacionamento = self.estacios[0]
        estacio.valores_hora.append(ValorHoraFactory.build(veiculo=self.veiculos[1]))

        self._test_general_edit_ok(self.adm_estacio_sess, veiculo=str(self.veiculos[1].id))

        valores = self.session.query(ValorHora).filter(ValorHora.estacio_fk == estacio.id).all()
        self.assertEqual(1, len(valores), 'Should only edit - not add - the valor hora')

    def test_edit_valor_hora_valor_invalido(self):
        for v in ['-1', '-0.05', '0']:
            success, error = self.repo.edit_valor_hora(self.adm_estacio_sess, self.session, self.veiculos[0].id,
                                                       Decimal(v))

            self.assertEqual('valor_nao_positivo', error, 'Error should be "valor_nao_positivo"')
            self.assertEqual(False, success, 'Success should be False')