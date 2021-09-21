import pathlib
import unittest
from collections import namedtuple
from unittest.mock import Mock, ANY

from src.classes.file_stream import MemoryFileStream
from src.container import create_container
from src.enums import UploadStatus
from src.models import AdminSistema, AdminEstacio, PedidoCadastro, Endereco
from src.repo import PedidoCadastroRepo
from tests.factories import set_session, BaseEnderecoFactory, UploadFactory
from tests.utils import make_engine, make_general_db_setup, get_adm_sistema, get_adm_estacio, make_savepoint, \
    singleton_provider, general_db_teardown, MockedCached


class TestPedidoCadastroRepo(unittest.TestCase):
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
        self.cached = MockedCached(self.container)
        self.container.cached.override(singleton_provider(self.cached))

        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        set_session(self.session)  # Factories

        self.crypto = self.container.crypto()

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(self.crypto, self.session)
        self.valid_adm, self.valid_adm_sess = get_adm_estacio(self.crypto, self.session)

        self.session.commit()
        make_savepoint(self.conn, self.session)

        self.uploader = Mock()
        self.container.uploader.override(singleton_provider(self.uploader))
        self.image_processor = Mock()
        self.container.image_processor.override(singleton_provider(self.image_processor))

        self.repo = PedidoCadastroRepo()

        self.upload = UploadFactory(sub_dir='foto_estacio', status=UploadStatus.CONCLUIDO)

        self.ret_fstream = Mock()
        self.image_processor.compress.return_value = self.ret_fstream
        self.uploader.upload.return_value = (True, self.upload)

        self.file_data = b'abc'
        self.fstream = MemoryFileStream(self.file_data)
        self.endereco = BaseEnderecoFactory()

        self.nome = 'Estacionamento de Teste'
        self.telefone = '+55123456789034'

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

        self.cached.clear_all()

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        admin_estacio = self.session.query(AdminEstacio).all()

        self.assertEqual([self.adm_sis], admin_sis)
        self.assertEqual([self.valid_adm], admin_estacio)

    def test_create_ok(self):
        Arg = namedtuple('Arg', 'u_sess nome tel endereco fstream')
        Ret = namedtuple('Ret', 'user nome tel img_proc_call upload_call foto')

        _u = [get_adm_estacio(self.crypto, self.session, n=n) for n in range(1, 20)]

        datas = [
            (Arg(_u[0][1], self.nome, self.telefone, self.endereco, self.fstream),
             Ret(_u[0][0], None, None, self.fstream, self.ret_fstream, self.upload)),
            (Arg(_u[1][1], 'A' * 100, self.telefone, self.endereco, self.fstream),
             Ret(_u[1][0], None, None, self.fstream, self.ret_fstream, self.upload)),
            (Arg(_u[2][1], self.nome, '+' + '1'*19, self.endereco, self.fstream),
             Ret(_u[2][0], None, None, self.fstream, self.ret_fstream, self.upload)),
            (Arg(_u[3][1], '  Teste   Nome' + ' '*100, self.telefone, self.endereco, self.fstream),
             Ret(_u[3][0], 'Teste   Nome', None, self.fstream, self.ret_fstream, self.upload)),
            (Arg(_u[4][1], self.nome, '   +5512345678901' + ' '*100, self.endereco, self.fstream),
             Ret(_u[4][0], None, '+5512345678901', self.fstream, self.ret_fstream, self.upload))
        ]

        for i in range(len(datas)):
            arg, ret = datas[i]
            ret = Ret(ret.user, ret.nome or arg.nome, ret.tel or arg.tel, ret.img_proc_call, ret.upload_call, ret.foto)

            success, obj = self.repo.create(arg.u_sess, self.session, arg.nome, arg.tel,
                                            arg.endereco, arg.fstream)
            self.assertEqual(True, success, f'Success should be True on {i}. Error: {obj}')
            self.assertEqual(ret.nome, obj.nome, f'Nomes should match on {i}')
            self.assertEqual(ret.tel, obj.telefone, f'Telefones should match on {i}')
            self.assertEqual(arg.endereco, obj.endereco, f'Enderecos should match on {i}')
            self.assertEqual(ret.user, obj.admin_estacio, f'Should set the admin estacio on {i}')

            self.image_processor.compress.assert_called_once_with(ret.img_proc_call)
            self.uploader.upload.assert_called_once_with(ret.upload_call, 'foto_estacio', ANY)

            self.assertEqual(ret.foto, obj.foto, f'Foto should be the upload on on {i}')

            self.assertEqual(self.session.query(PedidoCadastro).get(obj.id), obj,
                             f'Should add the obj to the session on {i}')
            self.assertEqual(self.session.query(Endereco).get(obj.endereco.id), arg.endereco,
                             f'Should add the endereco to the db on {i}')

            self.image_processor.reset_mock()
            self.uploader.reset_mock()

    def test_create_invalid_login(self):
        for user_sess in [self.adm_sis_sess, None]:
            success, error = self.repo.create(user_sess, self.session, self.nome, self.telefone, self.endereco,
                                              self.fstream)

            self.assertEqual(False, success, 'Success should be False')
            self.assertEqual('sem_permissao', error, 'Error should be "sem_permissao"')

            self.uploader.upload.assert_not_called()
            self.image_processor.compress.assert_not_called()

    def test_create_name_too_big(self):
        nomes = ['A' * 101, 'ABC' * 55]

        for nome in nomes:
            success, error = self.repo.create(self.valid_adm_sess, self.session, nome, self.telefone, self.endereco,
                                              self.fstream)

            self.assertEqual(False, success, 'Success should be False')
            self.assertEqual('nome_muito_grande', error, 'Error should be "nome_muito_grande"')

            self.uploader.upload.assert_not_called()
            self.image_processor.compress.assert_not_called()

    def test_create_telefone_invalido(self):
        tipos = {
            'telefone_formato_invalido': ['+551234abcdefsf', 'asdasd', '+55 (11) 12345-6789',
                                          '-5511123456789', '+551234-56789012', '', '      ', '+'],
            'telefone_sem_cod_internacional': ['16123456789', '5511123456789', '+5', '5555'],
            'telefone_muito_grande': ['+55' + '1' * 30, '+55' + '1' * 18]
        }

        for ret_error, tests in tipos.items():
            for i in range(len(tests)):
                tel = tests[i]

                success, error = self.repo.create(self.valid_adm_sess, self.session, self.nome, tel,
                                                  self.endereco, self.fstream)

                self.assertEqual(False, success, f'Success should be False on "{ret_error}:{i}"')
                self.assertEqual(ret_error, error, f'Error should be "{ret_error}" on {i}')

                self.uploader.upload.assert_not_called()
                self.image_processor.compress.assert_not_called()

    def test_create_foto_invalida(self):
        self.image_processor.compress.side_effect = AttributeError('File stream does not contain a valid image')

        success, error = self.repo.create(self.valid_adm_sess, self.session, self.nome, self.telefone, self.endereco,
                                          self.fstream)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('foto_formato_invalido', error, 'Error should be "foto_formato_invalido"')

        self.uploader.upload.assert_not_called()
        self.image_processor.compress.assert_called_once_with(self.fstream)

    def test_create_error_upload(self):
        self.uploader.upload.side_effect = Exception('Erro aleatorio')

        success, error = self.repo.create(self.valid_adm_sess, self.session, self.nome, self.telefone, self.endereco,
                                          self.fstream)

        self.assertEqual(False, success, 'Success should be False')
        self.assertEqual('upload_error', error, 'Error should be "upload_error"')

        self.image_processor.compress.assert_called_once_with(self.fstream)
        self.uploader.upload.assert_called_once_with(self.ret_fstream, 'foto_estacio', ANY)

        c = self.session.query(PedidoCadastro).count()
        self.assertEqual(0, c, 'There should not be any pedido added to the db')
        c = self.session.query(Endereco).count()
        self.assertEqual(0, c, 'There should not be any endereco added to the db')

    def test_create_one_admin_make_two_requests(self):
        success, pedido = self.repo.create(self.valid_adm_sess, self.session, self.nome, self.telefone,
                                           self.endereco, self.fstream)

        self.assertEqual(True, success, f'Success should be True. Error: {pedido}')

        self.uploader.reset_mock()
        self.image_processor.reset_mock()

        success, error = self.repo.create(self.valid_adm_sess, self.session, self.nome + 'x', self.telefone + '1',
                                          self.endereco, self.fstream)

        self.assertEqual(False, success, 'Success should be False on the second request')
        self.assertEqual('limite_pedido_atingido', error, 'Error should be "limite_pedido_atingido"')

        self.uploader.upload.assert_not_called()
        self.image_processor.compress.assert_not_called()


if __name__ == '__main__':
    unittest.main()
