import unittest

from tests.test_repo.test_estacionamento_crud_repo.base import BaseTestEstacioCrudRepo
from tests.utils.get_login import get_adm_estacio


class TestEstacioCrudRepoList(BaseTestEstacioCrudRepo):
    def test_list_all_ok(self):
        success, all_estacios = self.repo.list(self.session)

        self.assertEqual(True, success, 'Success should be True')
        self.assertSequenceEqual(self.estacios, all_estacios, 'Should return all estacios')

    def test_list_amount_ok(self):
        success, estacios = self.repo.list(self.session, amount=2)

        self.assertEqual(True, success, 'Success should be True')
        self.assertEqual(2, len(estacios), 'Should return exactly 2 items')
        self.assertSequenceEqual(self.estacios[:2], estacios, 'Should return exactly the first two estacios')

    def test_list_index_ok(self):
        success, estacios = self.repo.list(self.session, index=3)

        self.assertEqual(True, success, 'Success should be True')
        self.assertSequenceEqual(self.estacios[3:], estacios, 'Should return all estacios starting from the 3rd one')

    def test_list_index_and_amount_ok(self):
        success, estacios = self.repo.list(self.session, amount=2, index=3)

        self.assertEqual(True, success, 'Success should be True')
        self.assertSequenceEqual(self.estacios[3:5], estacios, 'Should return exactly the third and fourth estacios')

    def test_list_amount_more_than_created_or_negative(self):
        _cases = [10000, -5]
        for i in range(len(_cases)):
            success, estacios = self.repo.list(self.session, amount=_cases[i])

            self.assertEqual(True, success, f'Success should be True on {i}')
            self.assertSequenceEqual(self.estacios, estacios, f'Should return all pedidos on {i}')

    def test_list_index_out_of_range(self):
        _cases = [100, -1]

        for i in range(len(_cases)):
            success, estacios = self.repo.list(self.session, index=_cases[i])

            self.assertEqual(True, success, f'Success should be True on {i}')
            self.assertSequenceEqual([], estacios, f'Estacios should be an empty list on {i}')

    def test_get_ok(self):
        real_estacio = self.estacios[0]

        success, estacio = self.repo.get(None, self.session, str(real_estacio.id))

        self.assertEqual(True, success, 'Success should be True')
        self.assertEqual(real_estacio, estacio, 'Estacios should match')

    def test_get_not_found(self):
        _cases = ['1000', '-1', 'asdsadasd']
        for i in range(len(_cases)):
            success, error = self.repo.get(None, self.session, _cases[i])

            self.assertEqual(False, success, f'Success should be False on {i}')
            self.assertEqual('estacio_nao_encontrado', error, f'Error should be "estacio_nao_encontrado" on {i}')

    def test_get_adm_estacio_ok(self):
        real_estacio = self.estacios[1]

        success, estacio = self.repo.get(self.adm_estacio_edit_sess, self.session)

        self.assertEqual(True, success, f'Success should be True. Error: {estacio}')
        self.assertEqual(real_estacio, estacio, 'Estacios should match')

    def test_get_adm_estacio_ignore_default(self):
        real_estacio = self.estacios[0]

        success, estacio = self.repo.get(self.adm_estacio_edit_sess, self.session, estacio_id=str(real_estacio.id))

        self.assertEqual(True, success, f'Success should be True. Error: {estacio}')
        self.assertEqual(real_estacio, estacio, 'Estacios should match')

    def test_get_adm_estacio_no_estacio(self):
        adm_estacio, adm_estacio_sess = get_adm_estacio(self.crypto, self.session, n=98751)
        
        success, error = self.repo.get(adm_estacio_sess, self.session)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('estacio_nao_encontrado', error, 'Error should be "estacio_nao_encontrado"')

    def test_get_not_adm_estacio_no_id(self):
        _sess = [None, self.adm_sis_sess]

        for i in range(len(_sess)):
            success, error = self.repo.get(_sess[i], self.session)

            self.assertEqual('estacio_nao_encontrado', error, 'Error should be "estacio_nao_encontrado"')
            self.assertEqual(False, success, 'Success should be False')


if __name__ == '__main__':
    unittest.main()
