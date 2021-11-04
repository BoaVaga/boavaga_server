import unittest
from unittest.mock import ANY

from sqlalchemy.sql.expression import desc

from src.enums import UserType
from src.models import Estacionamento, Upload
from src.models.endereco import Endereco
from tests.factories.factory import EnderecoFactory
from tests.test_repo.test_estacionamento_crud_repo.base import BaseTestEstacioCrudRepo


_DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')


class TestEstacionamentoCrudRepoEdit(BaseTestEstacioCrudRepo):
    def _general_test_edit_ok(self, adm_sess, estacio='def', nome=None, telefone=None, endereco=None,
                              total_vaga=None, descricao=None, foto=None, estacio_id='def'):
        estacio = self.estacios[1] if estacio == 'def' else estacio
        if estacio_id == 'def':
            estacio_id = None if adm_sess.tipo == UserType.ESTACIONAMENTO else estacio.id
        exp_total_vaga = total_vaga or int(estacio.total_vaga)
        exp_qtd_vaga_livre = int(estacio.qtd_vaga_livre)
        if descricao is not None and descricao.startswith('~APAGAR'):
            exp_descricao = None
            descricao = descricao.replace('~APAGAR', '')
        else:
            exp_descricao = descricao or str(estacio.descricao)
            exp_descricao = exp_descricao.strip()

        exp_nome = nome or str(estacio.nome)
        exp_telefone = telefone or str(estacio.telefone)
        exp_endereco = endereco or estacio.endereco
        exp_endereco = Endereco.from_dict(exp_endereco.to_dict())
        ori_upload = self.copy_upload(estacio.foto)

        exp_nome = exp_nome.strip()

        ok, ret = self.repo.edit(adm_sess, self.session, nome=nome, telefone=telefone, endereco=endereco, 
                                total_vaga=total_vaga, descricao=descricao, foto=foto, estacio_id=estacio_id)

        self.assertEqual(True, ok, f'Success should be True. Error: {ret}')
        self.assertEqual(False, ret.esta_suspenso, 'Esta suspenso should be False')
        self.assertEqual(True, ret.esta_aberto, 'Esta aberto should be True')
        self.assertEqual(True, ret.cadastro_terminado, 'Cadastro terminado should be True')
        self.assertEqual(exp_nome, ret.nome, 'Nomes should match')
        self.assertEqual(exp_telefone, ret.telefone, 'Telefones should match')
        self.assertEqual(exp_endereco, ret.endereco, 'Enderecos should match')
        self.assertEqual(exp_total_vaga, ret.total_vaga, 'Total vaga should match')
        self.assertEqual(exp_qtd_vaga_livre, ret.qtd_vaga_livre, 'Qtd vaga livre should be maximum')
        self.assertEqual(exp_descricao, ret.descricao, 'Descricao should match')

        if foto is None:
            self.image_processor.compress.assert_not_called()
            self.uploader.upload.assert_not_called()
            self.uploader.delete.assert_not_called()
            self.assertEqual(ori_upload, ret.foto, 'Should keep the foto')
        else:
            self.image_processor.compress.assert_called_once_with(foto, 100, 100)
            self.uploader.upload.assert_called_once_with(self.ret_fstream, 'foto_estacio', ANY)
            self.uploader.delete.assert_called_once_with(ori_upload)

            self.assertEqual(self.base_upload, ret.foto, 'Foto should be the upload')

            self.assertIsNone(self.session.query(Upload).get(ori_upload.id), 'Should remove the original foto '
                                                                             'from the db')

        db_estacio = self.session.query(Estacionamento).get(estacio.id)
        self.assertEqual(estacio, db_estacio, 'Estacios should match on db level')

    def test_edit_with_adm_estacio_ok(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess)
    
    def test_edit_with_adm_sistema_ok(self):
        self._general_test_edit_ok(self.adm_sis_sess)

    def test_edit_nome_ok(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess, nome='Á'*100)

    def test_edit_telefone_ok(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess, telefone='+5516123456789')

    def test_edit_endereco_ok(self):
        endereco = EnderecoFactory.build()
        self._general_test_edit_ok(self.adm_estacio_edit_sess, endereco=endereco)

    def test_edit_total_vaga_1_ok(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess, total_vaga=1)

    def test_edit_descricao_quase_limite(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess, descricao=' ' + 'Á'*1998 + ' ')

    def test_edit_descricao_apagar(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess, descricao='~APAGAR')

    def test_edit_descricao_apagar_2(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess, descricao='~APAGAR ')

    def test_edit_foto_ok(self):
        self._general_test_edit_ok(self.adm_estacio_edit_sess, foto=self.fstream)

    def test_edit_ignore_estacio_id_with_adm_estacio(self):
        estacio = self.estacios[1]
        estacio_id = str(self.estacios[0].id)
        self._general_test_edit_ok(self.adm_estacio_edit_sess, estacio=estacio, estacio_id=estacio_id)

    def test_edit_fail_total_vaga_invalid(self):
        for t_vaga in [0, -1, -1234]:
            ok, ret = self.repo.edit(self.adm_estacio_edit_sess, self.session, total_vaga=t_vaga)

            self.assertEqual('total_vaga_nao_positivo', ret, f'Error should be "total_vaga_nao_positivo" on {t_vaga}')
            self.assertEqual(False, ok, f'Success should be False on {t_vaga}')

    def test_edit_fail_descricao_muito_grande(self):
        d = 'A' * 2001

        ok, ret = self.repo.edit(self.adm_estacio_edit_sess, self.session, descricao=d)
        self.assertEqual('descricao_muito_grande', ret, 'Error should be "descricao_muito_grande"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_edit_no_permission(self):
        ok, ret = self.repo.edit(None, self.session)

        self.assertEqual('sem_permissao', ret, 'Error should be "sem_permissao"')
        self.assertEqual(False, ok, 'Success should be False')
    
    def test_edit_estacio_not_finished(self):
        self.estacios[1].cadastro_terminado = False

        ok, ret = self.repo.edit(self.adm_estacio_edit_sess, self.session)

        self.assertEqual('cadastro_nao_terminado', ret, 'Error should be "cadastro_nao_terminado"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_edit_estacio_not_found_adm_estacio(self):
        self.adm_estacio_edit.estacionamento = None

        ok, ret = self.repo.edit(self.adm_estacio_edit_sess, self.session)

        self.assertEqual('estacio_nao_encontrado', ret, 'Error should be "estacio_nao_encontrado"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_edit_estacio_not_found_adm_sis(self):
        ok, ret = self.repo.edit(self.adm_sis_sess, self.session)

        self.assertEqual('estacio_nao_encontrado', ret, 'Error should be "estacio_nao_encontrado"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_edit_nome_muito_grande(self):
        ok, ret = self.repo.edit(self.adm_estacio_edit_sess, self.session, nome='Á' * 101)

        self.assertEqual('nome_muito_grande', ret, 'Error should be "nome_muito_grande"')
        self.assertEqual(False, ok, 'Success should be False')

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
        ori_upload = self.copy_upload(self.estacios[1].foto)

        success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session, foto=self.fstream)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('upload_error', error, 'Error should be "upload_error"')

        self.image_processor.compress.assert_called_once_with(self.fstream, 100, 100)
        self.uploader.upload.assert_called_once_with(self.ret_fstream, 'foto_estacio', ANY)
        self.uploader.delete.assert_not_called()

        foto = self.session.query(Upload).get(self.estacios[1].foto_fk)
        self.assertEqual(ori_upload, foto, 'Should not change the foto on the db')

    def test_image_processing_fail(self):
        self.image_processor.compress.side_effect = Exception('Random error')

        success, error = self.repo.edit(self.adm_estacio_edit_sess, self.session, foto=self.fstream)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('foto_processing_error', error, 'Error should be "foto_processing_error"')

        self.uploader.upload.assert_not_called()
        self.image_processor.compress.assert_called_once_with(self.fstream, 100, 100)



if __name__ == '__main__':
    unittest.main()
