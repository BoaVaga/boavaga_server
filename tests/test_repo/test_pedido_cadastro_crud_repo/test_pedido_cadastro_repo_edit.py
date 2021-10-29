import random
import unittest
from collections import namedtuple
from unittest.mock import ANY

from src.classes import *  # To avoid cyclic imports
from src.models import PedidoCadastro, Endereco, Upload
from tests.factories.factory import PedidoCadastroFactory
from tests.test_repo.test_pedido_cadastro_crud_repo.base import BaseTestPedidoCadastroCrudRepo
from tests.utils import get_adm_estacio


class TestPedidoCadastroCrudRepoEdit(BaseTestPedidoCadastroCrudRepo):
    def test_edit_ok(self):
        user, user_sess = get_adm_estacio(self.crypto, self.session, n=134)

        FotoRet = namedtuple('FotoRet', 'img_proc_call upload_call foto')
        Ret = namedtuple('Ret', 'nome tel foto_ret')

        datas = [
            ({'nome': self.nome}, Ret(None, None, None)),
            ({'nome': 'A' * 100}, Ret(None, None, None)),
            ({'telefone': '+' + '1'*19}, Ret(None, None, None)),
            ({'nome': '  Teste   Nome' + ' '*100}, Ret('Teste   Nome', None, None)),
            ({'telefone': '   +5512345678901' + ' '*100}, Ret(None, '+5512345678901', None)),
            ({'endereco': self.endereco}, Ret(None, None, None)),
            ({'foto': self.fstream}, Ret(None, None, FotoRet(self.fstream, self.ret_fstream, self.upload))),
            ({'nome': self.nome, 'telefone': self.telefone, 'endereco': self.endereco, 'foto': self.fstream},
             Ret(None, None, FotoRet(self.fstream, self.ret_fstream, self.upload))),
            ({'nome': self.nome, 'telefone': self.telefone, 'foto': self.fstream, 'erro_delete': True},
             Ret(None, None, FotoRet(self.fstream, self.ret_fstream, self.upload)))
        ]

        for i in range(len(datas)):
            num_rejeicao = random.randint(1, 2)
            pedido = PedidoCadastroFactory.create(admin_estacio=user, num_rejeicoes=num_rejeicao, msg_rejeicao='A')
            ori_foto_id, ori_end_id = int(pedido.foto_fk), int(pedido.endereco_fk)
            ori_upload = self.copy_upload(pedido.foto)

            arg_dct, ret = datas[i]
            ret = Ret(ret.nome or arg_dct.get('nome') or str(pedido.nome),
                      ret.tel or arg_dct.get('telefone') or str(pedido.telefone), ret.foto_ret)
            expect_endereco = arg_dct.get('endereco') or pedido.endereco

            if 'erro_delete' in arg_dct:
                self.uploader.delete.side_effect = Exception('Random error on uploader.delete')
                del arg_dct['erro_delete']

            success, obj = self.repo.edit(user_sess, self.session, **arg_dct)
            self.assertEqual(True, success, f'Success should be True on {i}. Error: {obj}')
            self.assertEqual(ret.nome, obj.nome, f'Nomes should match on {i}')
            self.assertEqual(ret.tel, obj.telefone, f'Telefones should match on {i}')

            self.assertEqual(ori_end_id, obj.endereco.id, f'Should use the same endereco id on {i}')
            expect_endereco.id = ori_end_id
            self.assertEqual(expect_endereco, obj.endereco, f'Enderecos should match on {i}')

            self.assertEqual(user, obj.admin_estacio, f'Should keep the admin estacio on {i}')
            self.assertEqual(num_rejeicao, obj.num_rejeicoes, f'Num rejeicoes should not change on {i}')
            self.assertIsNone(obj.msg_rejeicao, f'Msg rejeicao should be null on {i}')

            ret_foto: FotoRet = ret.foto_ret
            if ret_foto:
                self.image_processor.compress.assert_called_once_with(ret_foto.img_proc_call, 100, 100)
                self.uploader.upload.assert_called_once_with(ret_foto.upload_call, 'foto_estacio', ANY)
                self.uploader.delete.assert_called_once_with(ori_upload)

                self.assertEqual(ret_foto.foto, obj.foto, f'Foto should be the upload on {i}')

                self.assertIsNone(self.session.query(Upload).get(ori_foto_id), f'Should remove the original foto '
                                                                               f'from the db on {i}')
            else:
                self.image_processor.compress.assert_not_called()
                self.uploader.upload.assert_not_called()
                self.uploader.delete.assert_not_called()
                self.assertEqual(ori_foto_id, obj.foto.id, f'Should keep the same foto on {i}')

            self.assertEqual(self.session.query(PedidoCadastro).get(obj.id), obj,
                             f'Should add the obj to the session on {i}')
            self.assertEqual(self.session.query(Endereco).get(obj.endereco.id), expect_endereco,
                             f'Should add the endereco to the db on {i}')

            self.image_processor.reset_mock()
            self.uploader.reset_mock()

            self.session.delete(pedido)

    def test_edit_invalid_login(self):
        for user_sess in [self.adm_sis_sess, None]:
            success, error = self.repo.edit(user_sess, self.session, self.nome, self.telefone, self.endereco,
                                            self.fstream)

            self.assertEqual(False, success, 'Success should be False')
            self.assertEqual('sem_permissao', error, 'Error should be "sem_permissao"')

            self.uploader.upload.assert_not_called()
            self.image_processor.compress.assert_not_called()

    def test_edit_name_too_big(self):
        nomes = ['A' * 101, 'ABC' * 55]

        for nome in nomes:
            success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session, nome=nome)

            self.assertEqual(False, success, 'Success should be False')
            self.assertEqual('nome_muito_grande', error, 'Error should be "nome_muito_grande"')

            self.uploader.upload.assert_not_called()
            self.image_processor.compress.assert_not_called()

    def test_edit_telefone_invalido(self):
        tipos = {
            'telefone_formato_invalido': ['+551234abcdefsf', 'asdasd', '+55 (11) 12345-6789',
                                          '-5511123456789', '+551234-56789012', '      ', '+'],
            'telefone_sem_cod_internacional': ['16123456789', '5511123456789', '+5', '5555'],
            'telefone_muito_grande': ['+55' + '1' * 30, '+55' + '1' * 18]
        }

        for ret_error, tests in tipos.items():
            for i in range(len(tests)):
                tel = tests[i]

                success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session, telefone=tel)

                self.assertEqual(False, success, f'Success should be False on "{ret_error}:{i}"')
                self.assertEqual(ret_error, error, f'Error should be "{ret_error}" on {i}')

                self.uploader.upload.assert_not_called()
                self.image_processor.compress.assert_not_called()

    def test_edit_foto_invalida(self):
        self.image_processor.compress.side_effect = AttributeError('File stream does not contain a valid image')

        success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session, foto=self.fstream)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('foto_formato_invalido', error, 'Error should be "foto_formato_invalido"')

        self.uploader.upload.assert_not_called()
        self.image_processor.compress.assert_called_once_with(self.fstream, 100, 100)

    def test_edit_error_upload(self):
        self.uploader.upload.side_effect = Exception('Erro aleatorio')
        ori_upload = self.copy_upload(self.pedidos[0].foto)

        success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session, foto=self.fstream)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('upload_error', error, 'Error should be "upload_error"')

        self.image_processor.compress.assert_called_once_with(self.fstream, 100, 100)
        self.uploader.upload.assert_called_once_with(self.ret_fstream, 'foto_estacio', ANY)
        self.uploader.delete.assert_not_called()

        foto = self.session.query(Upload).get(self.pedidos[0].foto_fk)
        self.assertEqual(ori_upload, foto, 'Should not change the foto on the db')

    def test_edit_admin_has_no_pedido(self):
        success, error = self.repo.edit(self.adm_estacio_sess, self.session)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('sem_pedido', error, 'Error should be "sem_pedido"')

    def test_image_processing_fail(self):
        self.image_processor.compress.side_effect = Exception('Random error')

        success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session, foto=self.fstream)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('foto_processing_error', error, 'Error should be "foto_processing_error"')

        self.uploader.upload.assert_not_called()
        self.image_processor.compress.assert_called_once_with(self.fstream, 100, 100)

    def test_exceeded_limit_pedido(self):
        self.pedidos[0].num_rejeicoes = 10

        success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('max_num_rejeicoes_atingido', error, 'Error should be "max_num_rejeicoes_atingido"')

    def test_no_need_to_edit_error(self):
        self.pedidos[0].msg_rejeicao = None

        success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('nao_analisado_ainda', error, 'Error should be "nao_analisado_ainda"')


if __name__ == '__main__':
    unittest.main()
