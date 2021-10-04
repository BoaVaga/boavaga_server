import json
import unittest
from collections import namedtuple
from io import BytesIO

from sgqlc.operation import Operation
from sgqlc.types import Variable, Arg, non_null

from src.enums import UploadStatus
from src.models import PedidoCadastro, Endereco, Upload
from tests.factories import EnderecoFactory
from tests.test_api.nodes import Mutation, Upload as UploadType
from tests.test_api.test_pedido_cadastro_api.base import BaseTestPedidoCadastroApi


class TestPedidoCadastroCreateApi(BaseTestPedidoCadastroApi):
    def test_create_ok(self):
        nome, telefone = 'Estacio Teste', '+5512345678901'
        endereco = EnderecoFactory.build()
        endereco_dct = endereco.to_dict()
        foto_stream = BytesIO(b'abc')
        foto = Upload(nome_arquivo='abc.jpg', sub_dir='foto_estacio', status=UploadStatus.CONCLUIDO)
        foto_url = 'foto_estacio/abc.jpg'

        self.repo.create.return_value = (True, PedidoCadastro(id=341, nome=nome, telefone=telefone, endereco=endereco,
                                                              foto=foto))

        mutation = Operation(Mutation, variables={'foto': Arg(non_null(UploadType))})
        mutation.create_pedido_cadastro(nome=nome, telefone=telefone, endereco=endereco_dct, foto=Variable('foto'))

        js_str = json.dumps({'variables': {'foto': None}, 'query': mutation.__to_graphql__(auto_select_depth=5)})
        response = self.client.post('/graphql', content_type='multipart/form-data',
                                    data={'operations': js_str, 'map': '{"0":["variables.foto"]}',
                                          '0': (foto_stream, '0')})
        data = self.check_response(response, 'createPedidoCadastro')

        self.assertIsNone(data['error'], f'Error should be null')
        self.assertEqual(True, data['success'], f'Success should be True')

        pedido = data['pedidoCadastro']

        self.assertIsNotNone(pedido, 'Pedido should not be null')
        self.assertEqual('341', pedido['id'], 'IDs should match')
        self.assertEqual(nome, pedido['nome'], 'Nomes should match')
        self.assertEqual(telefone, pedido['telefone'], 'Telefones should match')

        endereco_ret = pedido['endereco']
        self.assert_endereco_equal(endereco, endereco_ret)

        self.assertEqual(foto_url, pedido['foto'], 'Fotos url should match')

    def test_create_errors(self):
        end_dct = EnderecoFactory.build().to_dict()

        for error in ['nome_muito_grande', 'sem_permissao', 'telefone_formato_invalido',
                      'telefone_sem_cod_internacional', 'telefone_muito_grande', 'foto_formato_invalido',
                      'upload_error', 'limite_pedido_atingido', 'foto_processing_error', None]:
            foto_stream = BytesIO(b'abc')

            self.repo.create.reset_mock()
            if error is None:
                self.repo.create.side_effect = Exception('Random Error')
                error = 'erro_desconhecido'
            else:
                self.repo.create.return_value = (False, error)

            mutation = Operation(Mutation, variables={'foto': Arg(non_null(UploadType))})
            mutation.create_pedido_cadastro(nome='Teste', telefone='+5511981845155', endereco=end_dct,
                                            foto=Variable('foto'))

            js_str = json.dumps({'variables': {'foto': None}, 'query': mutation.__to_graphql__(auto_select_depth=5)})
            response = self.client.post('/graphql', content_type='multipart/form-data',
                                        data={'operations': js_str, 'map': '{"0":["variables.foto"]}',
                                              '0': (foto_stream, '0')})
            data = self.check_response(response, 'createPedidoCadastro')

            self.assertEqual(error, data['error'], f'Errors should match on "{error}"')
            self.assertEqual(False, data['success'], f'Should return False on "{error}')

    def test_endereco_validation_fail(self):
        caso_teste = namedtuple('CasoTeste', 'attr values')
        _attrs = ('logradouro', 'cidade', 'bairro', 'numero')

        cases = {f'end_{attr}_vazio': caso_teste(attr, ('', '         ')) for attr in [*_attrs, 'cep']}
        max_len_attr = {
            'logradouro': 101, 'cidade': 51, 'bairro': 51, 'numero': 11
        }
        cases.update({f'end_{attr}_muito_grande': caso_teste(attr, ['A' * v]) for attr, v in max_len_attr.items()})
        cases['end_cep_invalido'] = caso_teste('cep', ['A'*8, 'A1111111', '12345 678', '12345-678', '-12345678', '1'*9,
                                                       '+12345678', '12345.678', '-1234567', '+1234567', '12345.67'])

        base_end_dct = EnderecoFactory.build().to_dict()
        self.repo.create.return_value = (False, 'should_not_call_create')

        for error, caso in cases.items():
            for i in range(len(caso.values)):
                foto_stream = BytesIO(b'abc')
                end_dct = dict(base_end_dct)

                if caso.values[i] is not None:
                    end_dct[caso.attr] = caso.values[i]
                else:
                    del end_dct[caso.attr]

                mutation = Operation(Mutation, variables={'foto': Arg(non_null(UploadType))})
                mutation.create_pedido_cadastro(nome='Teste', telefone='+5511981845155', endereco=end_dct,
                                                foto=Variable('foto'))

                js_str = json.dumps({'variables': {'foto': None}, 'query': str(mutation)})
                response = self.client.post('/graphql', content_type='multipart/form-data',
                                            data={'operations': js_str, 'map': '{"0":["variables.foto"]}',
                                                  '0': (foto_stream, '0')})

                data = self.check_response(response, 'createPedidoCadastro')

                self.assertEqual(error, data['error'], f'Errors should match on "{error}:{i}"')
                self.assertEqual(False, data['success'], f'Should return False on "{error}:{i}')

    def test_endereco_validation_ok(self):
        nome, telefone = 'Estacio Teste', '+5512345678901'
        _attrs = ('logradouro', 'cidade', 'bairro', 'numero', 'cep')

        max_len_attr = {
            'logradouro': 100, 'cidade': 50, 'bairro': 50, 'numero': 10, 'cep': 8
        }
        cases = {attr: [('A'*v, 'A'*v), (' '*v + 'A' + ' '*v, 'A')] for attr, v in max_len_attr.items()}
        cases['cep'] = [('12345678', '12345678'), ('       12345678   ', '12345678')]

        base_end_dct = EnderecoFactory.build().to_dict()
        self.repo.create.return_value = (False, 'should_not_call_create')

        for attr, values in cases.items():
            for i in range(len(values)):
                foto_stream = BytesIO(b'abc')
                foto = Upload(nome_arquivo='abc.jpg', sub_dir='foto_estacio', status=UploadStatus.CONCLUIDO)

                end_dct = dict(base_end_dct)

                test_value, real_value = values[i]
                end_dct[attr] = test_value

                end_obj = Endereco.from_dict(end_dct)
                setattr(end_obj, attr, real_value)

                self.repo.create.return_value = (True, PedidoCadastro(id=341, nome=nome, telefone=telefone,
                                                                      endereco=end_obj, foto=foto))

                mutation = Operation(Mutation, variables={'foto': Arg(non_null(UploadType))})
                mutation.create_pedido_cadastro(nome='Teste', telefone='+5511981845155', endereco=end_dct,
                                                foto=Variable('foto'))

                js_str = json.dumps({'variables': {'foto': None}, 'query': mutation.__to_graphql__(auto_select_depth=5)})
                response = self.client.post('/graphql', content_type='multipart/form-data',
                                            data={'operations': js_str, 'map': '{"0":["variables.foto"]}',
                                                  '0': (foto_stream, '0')})

                data = self.check_response(response, 'createPedidoCadastro')

                self.assertIsNone(data['error'], f'Error should be null on "{attr}:{i}"')
                self.assertEqual(True, data['success'], f'Should return True on "{attr}:{i}')

                end_ret = data['pedidoCadastro']['endereco']

                self.assert_endereco_equal(end_obj, end_ret, f'"{attr}:{i}"')


if __name__ == '__main__':
    unittest.main()
