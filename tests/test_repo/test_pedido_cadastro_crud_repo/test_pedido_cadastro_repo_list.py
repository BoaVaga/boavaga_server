import unittest

from tests.test_repo.test_pedido_cadastro_crud_repo.base import BaseTestPedidoCadastroCrudRepo


class TestPedidoCadastroCrudRepoList(BaseTestPedidoCadastroCrudRepo):
    def test_list_all_ok(self):
        success, all_pedidos = self.repo.list(self.adm_sis_sess, self.session)

        self.assertEqual(True, success, 'Success should be True')
        self.assertSequenceEqual(self.pedidos, all_pedidos, 'Should return all pedidos')

    def test_list_amount_ok(self):
        success, pedidos = self.repo.list(self.adm_sis_sess, self.session, amount=2)

        self.assertEqual(True, success, 'Success should be True')
        self.assertSequenceEqual(self.pedidos[:2], pedidos, 'Should return exactly the first two pedidos')

    def test_list_index_ok(self):
        success, pedidos = self.repo.list(self.adm_sis_sess, self.session, index=3)

        self.assertEqual(True, success, 'Success should be True')
        self.assertSequenceEqual(self.pedidos[3:], pedidos, 'Should return all pedidos starting from the 3rd one')

    def test_list_index_and_amount_ok(self):
        success, pedidos = self.repo.list(self.adm_sis_sess, self.session, amount=2, index=3)

        self.assertEqual(True, success, 'Success should be True')
        self.assertSequenceEqual(self.pedidos[3:5], pedidos, 'Should return exactly the third and fourth pedidos')

    def test_list_amount_more_than_created_or_negative(self):
        _cases = [10000, -5]
        for i in range(len(_cases)):
            success, pedidos = self.repo.list(self.adm_sis_sess, self.session, amount=_cases[i])

            self.assertEqual(True, success, f'Success should be True on {i}')
            self.assertSequenceEqual(self.pedidos, pedidos, f'Should return all pedidos on {i}')

    def test_list_index_out_of_range(self):
        _cases = [100, -1]

        for i in range(len(_cases)):
            success, pedidos = self.repo.list(self.adm_sis_sess, self.session, index=_cases[i])

            self.assertEqual(True, success, f'Success should be True on {i}')
            self.assertSequenceEqual([], pedidos, f'Pedidos should be an empty list on {i}')

    def test_list_no_permission(self):
        _sessions = [self.adm_estacio_sess, None]

        for i in range(len(_sessions)):
            success, error = self.repo.list(_sessions[i], self.session)

            self.assertEqual(False, success, f'Success should be False on {i}')
            self.assertEqual('sem_permissao', error, f'Error should be "sem_permissao" on {i}')

    def test_get_ok(self):
        real_pedido = self.pedidos[0]

        success, pedido = self.repo.get(self.adm_sis_sess, self.session, str(real_pedido.id))

        self.assertEqual(True, success, 'Success should be True')
        self.assertEqual(real_pedido, pedido, 'Pedidos should match')

    def test_get_not_found(self):
        _cases = ['1000', '-1']
        for i in range(len(_cases)):
            success, error = self.repo.get(self.adm_sis_sess, self.session, _cases[i])

            self.assertEqual(False, success, f'Success should be False on {i}')
            self.assertEqual('pedido_nao_encontrado', error, f'Error should be "pedido_nao_encontrado" on {i}')

    def test_get_no_permission(self):
        _sessions = [self.adm_estacio_sess, None]

        for i in range(len(_sessions)):
            success, error = self.repo.get(_sessions[i], self.session, str(self.pedidos[0].id))

            self.assertEqual(False, success, f'Success should be False on {i}')
            self.assertEqual('sem_permissao', error, f'Error should be "sem_permissao" on {i}')


if __name__ == '__main__':
    unittest.main()
