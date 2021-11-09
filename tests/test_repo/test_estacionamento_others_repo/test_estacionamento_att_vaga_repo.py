import unittest

from src.models import Estacionamento
from tests.test_repo.test_estacionamento_others_repo.base import BaseTestEstacioOthers


class TestEstacionamentoAttVagaRepo(BaseTestEstacioOthers):
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
