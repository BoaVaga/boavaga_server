import logging
from typing import Tuple, Union, Iterable, Optional
from uuid import uuid4

from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.classes import UserSession, FileStream
from src.container import Container
from src.enums import UserType
from src.models import Endereco, PedidoCadastro, AdminEstacio, Upload
from src.services import Uploader, ImageProcessor
from src.utils import validate_telefone


class PedidoCadastroCrudRepo:
    UPLOAD_GROUP = 'foto_estacio'
    ERRO_SEM_PERMISSAO = 'sem_permissao'
    ERRO_PEDIDO_NAO_ENCONTRADO = 'pedido_nao_encontrado'
    NOME_MUITO_GRANDE = 'nome_muito_grande'
    TEL_FORMATO_INV = 'telefone_formato_invalido'
    TEL_SEM_COD_INTER = 'telefone_sem_cod_internacional'
    TEL_MUITO_GRANDE = 'telefone_muito_grande'
    FOTO_FORMATO_INVALIDO = 'foto_formato_invalido'
    ERRO_UPLOAD = 'upload_error'
    LIMITE_PEDIDO_ERRO = 'limite_pedido_atingido'
    FOTO_PROCESSING_ERRO = 'foto_processing_error'
    ERRO_SEM_PEDIDO = 'sem_pedido'
    ERRO_LIMITE_TENTATIVAS = 'max_num_rejeicoes_atingido'
    ERRO_NAO_ANALISADO_AINDA = 'nao_analisado_ainda'

    @inject
    def __init__(
            self,
            width_foto: int,
            height_foto: int,
            limite_tentativas: int,
            uploader: Uploader = Provide[Container.uploader],
            image_processor: ImageProcessor = Provide[Container.image_processor]
    ):
        self.uploader = uploader
        self.image_processor = image_processor

        self.width_foto = width_foto
        self.height_foto = height_foto
        self.limite_tentativas = limite_tentativas

    def create(self, user_sess: UserSession, sess: Session, nome: str, telefone: str,
               endereco: Endereco, foto: Optional[FileStream] = None) -> Tuple[bool, Union[str, PedidoCadastro]]:
        if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.ERRO_SEM_PERMISSAO

        adm: AdminEstacio = user_sess.user
        if (adm.estacio_fk is not None
                or sess.query(PedidoCadastro).filter(PedidoCadastro.admin_estacio_fk == adm.id).count() > 0):
            return False, self.LIMITE_PEDIDO_ERRO

        nome = nome.strip()
        _val_nome = self._validate_nome(nome)
        if _val_nome:
            return False, _val_nome

        telefone = telefone.strip()
        _val_tel = self._validate_tel(telefone)
        if _val_tel:
            return False, _val_tel

        if foto is not None:
            success_upload, upload_or_error = self._process_and_upload(foto, 'create()')
            if not success_upload:
                return False, upload_or_error
        else:
            upload_or_error = None

        pedido = PedidoCadastro(nome=nome, telefone=telefone, endereco=endereco, foto=upload_or_error,
                                admin_estacio=user_sess.user)
        sess.add(pedido)
        sess.commit()

        return True, pedido

    def edit(
        self,
        user_sess: UserSession, sess: Session,
        nome: Optional[str] = None, telefone: Optional[str] = None,
        endereco: Optional[Endereco] = None, foto: Optional[FileStream] = None
    ) -> Tuple[bool, Union[str, PedidoCadastro]]:
        if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.ERRO_SEM_PERMISSAO

        adm = user_sess.user
        pedido: PedidoCadastro = adm.pedido_cadastro

        if pedido is None:
            return False, self.ERRO_SEM_PEDIDO
        if pedido.num_rejeicoes >= self.limite_tentativas:
            return False, self.ERRO_LIMITE_TENTATIVAS
        if pedido.msg_rejeicao is None:
            return False, self.ERRO_NAO_ANALISADO_AINDA

        if nome:
            nome = nome.strip()
            _val_nome = self._validate_nome(nome)
            if _val_nome:
                return False, _val_nome

            pedido.nome = nome.strip()
        if telefone:
            telefone = telefone.strip()
            _val_tel = self._validate_tel(telefone)
            if _val_tel:
                return False, _val_tel

            pedido.telefone = telefone.strip()
        if endereco:
            pedido.endereco.update(endereco)

        pedido.msg_rejeicao = None

        if foto:
            success_upload, upload_or_error = self._process_and_upload(foto, 'edit()')
            if not success_upload:
                return False, upload_or_error

            try:
                self.uploader.delete(pedido.foto)
            except Exception as ex:
                logging.getLogger(__name__).error('edit(): Error while deleting uploaded file.', exc_info=ex)

            ori_id = int(pedido.foto_fk)
            pedido.foto = upload_or_error

            sess.query(Upload).filter(Upload.id == ori_id).delete()

        sess.commit()

        return True, pedido

    def list(self, user_sess: UserSession, sess: Session, amount: int = 0, index: int = 0) \
            -> Tuple[bool, Union[str, Iterable[PedidoCadastro]]]:
        if user_sess is None or user_sess.tipo != UserType.SISTEMA:
            return False, self.ERRO_SEM_PERMISSAO

        if index < 0:
            return True, tuple()

        query = sess.query(PedidoCadastro).filter(
            PedidoCadastro.msg_rejeicao == None
        ).offset(index)

        if amount > 0:
            query = query.limit(amount)

        pedidos = query.all()

        return True, pedidos

    def get(self, user_sess: UserSession, sess: Session, pedido_id: Optional[str] = None) \
            -> Tuple[bool, Union[str, PedidoCadastro]]:
        if user_sess is None:
            return False, self.ERRO_SEM_PERMISSAO

        if user_sess.tipo == UserType.ESTACIONAMENTO:
            pedido = user_sess.user.pedido_cadastro
            if pedido is None:
                return False, self.ERRO_SEM_PEDIDO
            else:
                return True, pedido

        pedido = sess.query(PedidoCadastro).get(pedido_id)
        if pedido is None:
            return False, self.ERRO_PEDIDO_NAO_ENCONTRADO

        return True, pedido

    def _validate_nome(self, nome: str) -> Optional[str]:
        if len(nome) > 100:
            return self.NOME_MUITO_GRANDE

    def _validate_tel(self, tel: str) -> Optional[str]:
        if len(tel) > 20:
            return self.TEL_MUITO_GRANDE
        if not validate_telefone(tel):
            return self.TEL_FORMATO_INV
        if not tel.startswith('+') or len(tel) < 3:
            return self.TEL_SEM_COD_INTER

    def _process_and_upload(self, foto: FileStream, log: str) -> Tuple[bool, Union[str, Upload]]:
        try:
            ret = self.image_processor.compress(foto, self.width_foto, self.height_foto)
        except AttributeError:
            return False, self.FOTO_FORMATO_INVALIDO
        except Exception as ex:
            logging.getLogger(__name__).error(f'{log}: Image processing error.', exc_info=ex)
            return False, self.FOTO_PROCESSING_ERRO

        try:
            fname = str(uuid4()) + '.' + self.image_processor.get_default_image_format()
            upload = self.uploader.upload(ret, self.UPLOAD_GROUP, fname)
        except Exception as ex:
            logging.getLogger(__name__).error(f'{log}: Upload error.', exc_info=ex)
            return False, self.ERRO_UPLOAD

        return True, upload
