from typing import Tuple, Union
from uuid import uuid4

from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.classes import UserSession, FileStream
from src.container import Container
from src.enums import UserType
from src.models import Endereco, PedidoCadastro
from src.services import Uploader, ImageProcessor


class PedidoCadastroRepo:
    UPLOAD_GROUP = 'foto_estacio'
    ERRO_SEM_PERMISSAO = 'sem_permissao'

    @inject
    def __init__(self, uploader: Uploader = Provide[Container.uploader],
                 image_processor: ImageProcessor = Provide[Container.image_processor]):
        self.uploader = uploader
        self.image_processor = image_processor

    def create(self, user_sess: UserSession, sess: Session, nome: str, telefone: str,
               endereco: Endereco, foto: FileStream) -> Tuple[bool, Union[str, PedidoCadastro]]:
        if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.ERRO_SEM_PERMISSAO

        ret = self.image_processor.compress(foto)
        ok, upload = self.uploader.upload(ret, self.UPLOAD_GROUP, str(uuid4()))

        pedido = PedidoCadastro(nome=nome, telefone=telefone, endereco=endereco, foto=upload,
                                admin_estacio=user_sess.user)
        sess.add(pedido)
        sess.commit()

        return True, pedido
