import logging
import pathlib
import unittest
from unittest.mock import Mock

from src.classes.file_stream import MemoryFileStream
from src.container import create_container
from src.enums import UploadStatus
from src.models import AdminSistema, AdminEstacio, PedidoCadastro
from src.repo import PedidoCadastroRepo
from tests.factories import set_session, UploadFactory, PedidoCadastroFactory, EnderecoFactory
from tests.utils import make_engine, make_general_db_setup, get_adm_sistema, get_adm_estacio, make_savepoint, \
    singleton_provider, general_db_teardown, MockedCached


class BaseTestPedidoCadastro(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logging.basicConfig(level=logging.FATAL)

        config_path = str(pathlib.Path(__file__).parents[3] / 'test.ini')
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
        self.adm_estacio, self.adm_estacio_sess = get_adm_estacio(self.crypto, self.session)

        self.pedidos = PedidoCadastroFactory.create_batch(10)

        self.session.commit()
        make_savepoint(self.conn, self.session)

        self.uploader = Mock()
        self.container.uploader.override(singleton_provider(self.uploader))
        self.image_processor = Mock()
        self.container.image_processor.override(singleton_provider(self.image_processor))

        cfg = self.container.config.get('pedido_cadastro')
        self.repo = PedidoCadastroRepo(int(cfg['width_foto']), int(cfg['height_foto']))

        self.upload = UploadFactory(sub_dir='foto_estacio', status=UploadStatus.CONCLUIDO)

        self.ret_fstream = Mock()
        self.image_processor.compress.return_value = self.ret_fstream
        self.image_processor.get_default_image_format.return_value = 'png'

        self.uploader.upload.return_value = (True, self.upload)

        self.file_data = b'abc'
        self.fstream = MemoryFileStream(self.file_data)
        self.endereco = EnderecoFactory.build()

        self.nome = 'Estacionamento de Teste'
        self.telefone = '+55123456789034'

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

        self.cached.clear_all()

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        admin_estacio = self.session.query(AdminEstacio).all()
        pedidos = self.session.query(PedidoCadastro).all()

        self.assertEqual([self.adm_sis], admin_sis)
        self.assertIn(self.adm_estacio, admin_estacio)
        self.assertEqual(self.pedidos, pedidos)


if __name__ == '__main__':
    unittest.main()
