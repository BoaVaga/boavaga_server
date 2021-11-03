import pathlib
import unittest
from unittest.mock import Mock

from src.container import create_container
from src.enums import UploadStatus
from src.classes import MemoryFileStream
from src.models import AdminSistema, AdminEstacio, Estacionamento, Veiculo, Upload
from src.repo import EstacionamentoCrudRepo
from tests.factories import set_session, EstacionamentoFactory, VeiculoFactory, UploadFactory
from tests.utils import make_engine, make_general_db_setup, make_savepoint, get_adm_sistema, get_adm_estacio, \
    general_db_teardown, singleton_provider

_DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')


class BaseTestEstacioCrudRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = str(pathlib.Path(__file__).parents[3] / 'test.ini')
        cls.container = create_container(config_path)

        conn_string = str(cls.container.config.get('db')['conn_string'])
        cls.engine = make_engine(conn_string)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.maxDiff = 3000
        self.crypto = self.container.crypto()

        self.conn, self.outer_trans, self.session = make_general_db_setup(self.engine)
        set_session(self.session)  # Factories

        self.estacios = EstacionamentoFactory.create_batch(10, cadastro_terminado=False)
        self.veiculos = VeiculoFactory.create_batch(10)

        self.session.commit()

        make_savepoint(self.conn, self.session)

        self.adm_sis, self.adm_sis_sess = get_adm_sistema(self.crypto, self.session)
        self.adm_estacio, self.adm_estacio_sess = get_adm_estacio(self.crypto, self.session)
        self.adm_estacio.estacionamento = self.estacios[0]
        self.adm_estacio.admin_mestre = True

        self.adm_estacio_edit, self.adm_estacio_edit_sess = get_adm_estacio(self.crypto, self.session, n=9854)
        self.adm_estacio_edit.estacionamento = self.estacios[1]
        self.adm_estacio.admin_mestre = False
        self.estacios[1].cadastro_terminado = True

        self.base_upload = UploadFactory(sub_dir='foto_estacio', status=UploadStatus.CONCLUIDO)

        self.uploader = Mock()
        self.container.uploader.override(singleton_provider(self.uploader))
        self.image_processor = Mock()
        self.container.image_processor.override(singleton_provider(self.image_processor))

        self.ret_fstream = Mock()
        self.image_processor.compress.return_value = self.ret_fstream
        self.image_processor.get_default_image_format.return_value = 'png'

        self.uploader.upload.return_value = self.base_upload

        self.file_data = b'abc'
        self.fstream = MemoryFileStream(self.file_data)

        self.repo = EstacionamentoCrudRepo()

    def tearDown(self) -> None:
        general_db_teardown(self.conn, self.outer_trans, self.session)

    def test_setup(self):
        admin_sis = self.session.query(AdminSistema).all()
        admin_estacio = self.session.query(AdminEstacio).all()
        estacios = self.session.query(Estacionamento).all()
        veiculos = self.session.query(Veiculo).all()

        self.assertEqual([self.adm_sis], admin_sis)
        self.assertIn(self.adm_estacio, admin_estacio)
        self.assertEqual(self.estacios, estacios)
        self.assertEqual(self.veiculos, veiculos)

    @staticmethod
    def copy_upload(base_upload: Upload) -> Upload:
        return Upload(id=int(base_upload.id), nome_arquivo=base_upload.nome_arquivo,
                      sub_dir=str(base_upload.sub_dir), status=UploadStatus(base_upload.status.value))


if __name__ == '__main__':
    unittest.main()
