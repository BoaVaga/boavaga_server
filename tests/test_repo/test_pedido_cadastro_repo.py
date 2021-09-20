import pathlib
import unittest
from unittest.mock import Mock, ANY

from src.classes.file_stream import MemoryFileStream
from src.container import create_container
from src.enums import UploadStatus
from src.models import AdminSistema, AdminEstacio, PedidoCadastro
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

        crypto = self.container.crypto()

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(crypto, self.session)
        self.valid_adm, self.valid_adm_sess = get_adm_estacio(crypto, self.session)

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
        success, obj = self.repo.create(self.valid_adm_sess, self.session, self.nome, self.telefone,
                                        self.endereco, self.fstream)
        self.assertEqual(True, success, f'Success should be True. Error: {obj}')
        self.assertEqual(self.nome, obj.nome, 'Nomes should match')
        self.assertEqual(self.telefone, obj.telefone, 'Telefones should match')
        self.assertEqual(self.endereco, obj.endereco, 'Enderecos should match')
        self.assertEqual(self.valid_adm, obj.admin_estacio, 'Should set the admin estacio')

        self.image_processor.compress.assert_called_once_with(self.fstream)
        self.uploader.upload.assert_called_once_with(self.ret_fstream, 'foto_estacio', ANY)

        self.assertEqual(self.upload, obj.foto, 'Foto should be the upload')

        self.assertEqual(self.session.query(PedidoCadastro).get(obj.id), obj, f'Should add the obj to the session')

    def test_create_invalid_login(self):
        for user_sess in [self.adm_sis_sess, None]:
            success, error = self.repo.create(user_sess, self.session, self.nome, self.telefone, self.endereco,
                                              self.fstream)

            self.assertEqual(False, success, 'Success should be False')
            self.assertEqual('sem_permissao', error, 'Error should be "sem_permissao"')

            self.uploader.upload.assert_not_called()
            self.image_processor.compress.assert_not_called()


if __name__ == '__main__':
    unittest.main()
