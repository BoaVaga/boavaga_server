import unittest
from unittest.mock import ANY

from src.enums import UserType
from src.models import Estacionamento, Upload
from src.models.endereco import Endereco
from tests.test_repo.test_estacionamento_crud_repo.base import BaseTestEstacioCrudRepo


_DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')


class TestEstacionamentoCrudRepo(BaseTestEstacioCrudRepo):
    def _general_test_edit_ok(self, adm_sess, estacio='def', nome=None, telefone=None, endereco=None,
                              total_vaga=None, descricao=None, foto=None, estacio_id='def'):
        estacio = self.estacios[1] if estacio == 'def' else estacio
        if estacio_id == 'def':
            estacio_id = None if adm_sess.tipo == UserType.ESTACIONAMENTO else estacio.id
        exp_total_vaga = total_vaga or int(estacio.total_vaga)
        exp_qtd_vaga_livre = int(estacio.qtd_vaga_livre)
        exp_descricao = descricao or str(estacio.descricao)
        exp_nome = nome or str(estacio.nome)
        exp_telefone = telefone or str(estacio.telefone)
        exp_endereco = endereco or estacio.endereco
        exp_endereco = Endereco.from_dict(exp_endereco.to_dict())
        ori_upload = self.copy_upload(estacio.foto)

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

    '''def test_create_with_adm_estacio_ok(self):
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

    def test_create_ignore_estacio_id_with_adm_estacio(self):
        estacio = self.estacios[0]
        estacio_id = str(self.estacios[1].id)
        self._general_test_create_ok(self.adm_estacio_sess, estacio=estacio, estacio_id=estacio_id)

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

    def test_create_no_permission(self):
        ok, ret = self.repo.create(None, self.session, 5, HorarioPadraoFactory.build())

        self.assertEqual('sem_permissao', ret, 'Error should be "sem_permissao"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_create_estacio_already_finished(self):
        self.estacios[0].cadastro_terminado = True

        ok, ret = self.repo.create(self.adm_estacio_sess, self.session, 5, HorarioPadraoFactory.build())

        self.assertEqual('cadastro_ja_terminado', ret, 'Error should be "cadastro_ja_terminado"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_create_estacio_not_found_adm_estacio(self):
        self.adm_estacio.estacionamento = None

        ok, ret = self.repo.create(self.adm_estacio_sess, self.session, 5, HorarioPadraoFactory.build())

        self.assertEqual('estacio_nao_encontrado', ret, 'Error should be "estacio_nao_encontrado"')
        self.assertEqual(False, ok, 'Success should be False')

    def test_create_estacio_not_found_adm_sis(self):
        ok, ret = self.repo.create(self.adm_sis_sess, self.session, 5, HorarioPadraoFactory.build())

        self.assertEqual('estacio_nao_encontrado', ret, 'Error should be "estacio_nao_encontrado"')
        self.assertEqual(False, ok, 'Success should be False')'''


if __name__ == '__main__':
    unittest.main()
