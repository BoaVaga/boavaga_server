import logging
from typing import Tuple, Union
from uuid import uuid4

from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.classes import UserSession, FileStream
from src.container import Container
from src.enums import UserType
from src.models import Endereco, PedidoCadastro
from src.services import Uploader, ImageProcessor
from src.utils import validate_telefone


class PedidoCadastroRepo:
    UPLOAD_GROUP = 'foto_estacio'
    ERRO_SEM_PERMISSAO = 'sem_permissao'
    NOME_MUITO_GRANDE = 'nome_muito_grande'
    TEL_FORMATO_INV = 'telefone_formato_invalido'
    TEL_SEM_COD_INTER = 'telefone_sem_cod_internacional'
    TEL_MUITO_GRANDE = 'telefone_muito_grande'
    FOTO_FORMATO_INVALIDO = 'foto_formato_invalido'
    ERRO_UPLOAD = 'upload_error'
    LIMITE_PEDIDO_ERRO = 'limite_pedido_atingido'
    FOTO_PROCESSING_ERRO = 'foto_processing_error'

    @inject
    def __init__(
            self,
            width_foto: int,
            height_foto: int,
            uploader: Uploader = Provide[Container.uploader],
            image_processor: ImageProcessor = Provide[Container.image_processor]
    ):
        self.uploader = uploader
        self.image_processor = image_processor

        self.width_foto = width_foto
        self.height_foto = height_foto

    def create(self, user_sess: UserSession, sess: Session, nome: str, telefone: str,
               endereco: Endereco, foto: FileStream) -> Tuple[bool, Union[str, PedidoCadastro]]:
        if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.ERRO_SEM_PERMISSAO
        if sess.query(PedidoCadastro).filter(PedidoCadastro.admin_estacio_fk == user_sess.user_id).count() > 0:
            return False, self.LIMITE_PEDIDO_ERRO

        nome = nome.strip()
        if len(nome) > 100:
            return False, self.NOME_MUITO_GRANDE

        telefone = telefone.strip()
        if len(telefone) > 20:
            return False, self.TEL_MUITO_GRANDE
        if not validate_telefone(telefone):
            return False, self.TEL_FORMATO_INV
        if not telefone.startswith('+') or len(telefone) < 3:
            return False, self.TEL_SEM_COD_INTER

        try:
            ret = self.image_processor.compress(foto, self.width_foto, self.height_foto)
        except AttributeError:
            return False, self.FOTO_FORMATO_INVALIDO
        except Exception as ex:
            logging.getLogger(__name__).error(f'create(): Image processing error.', exc_info=ex)
            return False, self.FOTO_PROCESSING_ERRO

        try:
            fname = str(uuid4()) + '.' + self.image_processor.get_default_image_format()
            ok, upload = self.uploader.upload(ret, self.UPLOAD_GROUP, fname)
        except Exception as ex:
            logging.getLogger(__name__).error(f'create(): Upload error.', exc_info=ex)
            return False, self.ERRO_UPLOAD

        pedido = PedidoCadastro(nome=nome, telefone=telefone, endereco=endereco, foto=upload,
                                admin_estacio=user_sess.user)
        sess.add(pedido)
        sess.commit()

        return True, pedido
