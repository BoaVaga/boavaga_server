import unittest
from unittest.mock import ANY

from sgqlc.operation import Operation

from tests.test_api.nodes import Query
from tests.test_api.test_pedido_cadastro_api.base import BaseTestPedidoCadastroApi


class TestPedidoCadastroListApi(BaseTestPedidoCadastroApi):
    def test_get_ok(self):
        pedido_real = self.pedidos[0]
        self.repo.get.return_value = (True, pedido_real)

        query = Operation(Query)
        query.get_pedido_cadastro(pedido_id=pedido_real.id)

        response = self.client.post('/graphql', json={'query': query.__to_graphql__(auto_select_depth=5)})
        data = self.check_response(response, 'getPedidoCadastro')

        self.assertIsNone(data['error'], 'Error should be None')
        self.assertEqual(True, data['success'], 'Success should be True')

        self.assert_pedido_equal(pedido_real, data['pedidoCadastro'], 'Pedidos should match')
        self.repo.get.assert_called_once_with(self.user_sess, ANY, str(pedido_real.id))

    def test_get_adm_estacio_ok(self):
        pedido_real = self.pedidos[0]
        self.repo.get.return_value = (True, pedido_real)

        query = Operation(Query)
        query.get_pedido_cadastro()

        response = self.client.post('/graphql', json={'query': query.__to_graphql__(auto_select_depth=5)})
        data = self.check_response(response, 'getPedidoCadastro')

        self.assertIsNone(data['error'], 'Error should be None')
        self.assertEqual(True, data['success'], 'Success should be True')

        self.assert_pedido_equal(pedido_real, data['pedidoCadastro'], 'Pedidos should match')
        self.repo.get.assert_called_once_with(self.user_sess, ANY, None)

    def test_get_errors(self):
        for error in ['sem_permissao', 'pedido_nao_encontrado', 'sem_pedido', None]:
            self.repo.get.reset_mock()
            if error is None:
                self.repo.get.side_effect = Exception('Random Error')
                error = 'erro_desconhecido'
            else:
                self.repo.get.return_value = (False, error)

            query = Operation(Query)
            query.get_pedido_cadastro(pedido_id=str(self.pedidos[0].id))

            response = self.client.post('/graphql', json={'query': query.__to_graphql__(auto_select_depth=5)})
            data = self.check_response(response, 'getPedidoCadastro')

            self.assertEqual(error, data['error'], f'Error should be "{error}"')
            self.assertEqual(False, data['success'], 'Success should be False')
            self.assertIsNone(data['pedidoCadastro'], 'Pedido cadastro should be None')

    def test_list_ok(self):
        ret_list = self.pedidos[2:5]
        self.repo.list.return_value = (True, ret_list)

        query = Operation(Query)
        query.list_pedido_cadastro(amount=3, index=2)

        response = self.client.post('/graphql', json={'query': query.__to_graphql__(auto_select_depth=5)})
        data = self.check_response(response, 'listPedidoCadastro')

        self.repo.list.assert_called_once_with(self.user_sess, ANY, amount=3, index=2)

        self.assertIsNone(data['error'], 'Error should be None')
        self.assertEqual(True, data['success'], 'Success should be True')

        self.assert_count_equal_pedidos(ret_list, data['pedidosCadastro'], 'Pedidos should match.\n{}')

    def test_list_errors(self):
        for error in ['sem_permissao', 'pedido_nao_encontrado', None]:
            self.repo.list.reset_mock()
            if error is None:
                self.repo.list.side_effect = Exception('Random Error')
                error = 'erro_desconhecido'
            else:
                self.repo.list.return_value = (False, error)

            query = Operation(Query)
            query.list_pedido_cadastro(amount=3, index=2)

            response = self.client.post('/graphql', json={'query': query.__to_graphql__(auto_select_depth=5)})
            data = self.check_response(response, 'listPedidoCadastro')

            self.assertEqual(error, data['error'], f'Error should be "{error}"')
            self.assertEqual(False, data['success'], 'Success should be False')
            self.assertIsNone(data['pedidosCadastro'], 'Pedidos cadastro should be None')


if __name__ == '__main__':
    unittest.main()
