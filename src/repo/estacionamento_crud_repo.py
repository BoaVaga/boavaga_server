from typing import Optional, Iterable, Tuple, Union
import logging

from uuid import uuid4
from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.classes import UserSession, ValorHoraInput, FileStream
from src.enums import UserType
from src.exceptions import ValidationError
from src.models import HorarioPadrao, Estacionamento, Endereco, Upload
from src.services import Uploader, ImageProcessor
from src.container import Container
from src.utils import validate_telefone


class EstacionamentoCrudRepo:
    ERRO_TOTAL_VAGA_INV = 'total_vaga_nao_positivo'
    ERRO_HORA_P_INV = 'hora_padrao_fecha_depois_de_abrir'
    ERRO_DESC_GRANDE = 'descricao_muito_grande'
    ERRO_VALOR_HORA_NAO_POSITIVO = 'valor_hora_preco_nao_positivo'
    ERRO_VALOR_HORA_VEICULO_NAO_ENCONTRADO = 'valor_hora_veiculo_nao_encontrado'
    ERRO_SEM_PERMISSAO = 'sem_permissao'
    ERRO_CADASTRO_FINALIZADO = 'cadastro_ja_terminado'
    ERRO_ESTACIO_NAO_ENCONTRADO = 'estacio_nao_encontrado'
    ERRO_CADASTRO_NAO_FINALIZADO = 'cadastro_nao_terminado'
    ERRO_NOME_GRANDE = 'nome_muito_grande'
    TEL_MUITO_GRANDE = 'telefone_muito_grande'
    TEL_FORMATO_INV = 'telefone_formato_invalido'
    TEL_SEM_COD_INTER = 'telefone_sem_cod_internacional'
    FOTO_FORMATO_INVALIDO = 'foto_formato_invalido'
    FOTO_PROCESSING_ERRO = 'foto_processing_error'
    ERRO_UPLOAD = 'upload_error'

    GROUP_UPLOAD_FOTO = 'foto_estacio'

    @inject
    def __init__(
        self,
        width_foto: int,
        height_foto: int,
        uploader: Uploader = Provide[Container.uploader], 
        image_proc: ImageProcessor = Provide[Container.image_processor]
    ) -> None:
        self.width_foto = width_foto
        self.height_foto = height_foto
        self.uploader = uploader
        self.image_processor = image_proc

    def create(
        self, user_sess: UserSession, sess: Session,
        total_vaga: int,
        horario_padrao: HorarioPadrao,
        valores_hora: Optional[Iterable[ValorHoraInput]] = None,
        estacio_id: Optional[str] = None,
        descricao: Optional[str] = None
    ) -> Tuple[bool, Union[str, Estacionamento]]:
        if user_sess is None:
            return False, self.ERRO_SEM_PERMISSAO

        adm = user_sess.user            
        if user_sess.tipo == UserType.SISTEMA:
            estacio: Estacionamento = sess.query(Estacionamento).get(estacio_id)
        else:
            estacio: Estacionamento = adm.estacionamento

        if estacio is None:
            return False, self.ERRO_ESTACIO_NAO_ENCONTRADO

        if estacio.cadastro_terminado:
            return False, self.ERRO_CADASTRO_FINALIZADO

        _val_desc = self._validate_descricao(descricao)
        if _val_desc:
            return False, _val_desc

        _val_total = self._validate_total_vaga(total_vaga)
        if _val_total:
            return False, _val_total

        error_hora_p = horario_padrao.validate()
        if error_hora_p:
            return False, error_hora_p

        if valores_hora:
            try:
                real_valores_hora = [v.to_valor_hora(sess) for v in valores_hora]
                estacio.valores_hora = real_valores_hora
            except ValidationError as e:
                if e.attr == 'valor':
                    return False, self.ERRO_VALOR_HORA_NAO_POSITIVO
                else:
                    return False, self.ERRO_VALOR_HORA_VEICULO_NAO_ENCONTRADO

        estacio.total_vaga = estacio.qtd_vaga_livre = total_vaga
        estacio.descricao = descricao
        estacio.horario_padrao = horario_padrao
        estacio.cadastro_terminado = True

        sess.commit()

        return True, estacio

    def edit(        
        self, user_sess: UserSession, sess: Session,
        nome: Optional[str] = None,
        telefone: Optional[str] = None,
        endereco: Optional[Endereco] = None,
        total_vaga: Optional[int] = None,
        descricao: Optional[str] = None,
        foto: Optional[FileStream] = None,
        estacio_id: Optional[str] = None,
    ) -> Tuple[bool, Union[str, Estacionamento]]:
        if user_sess is None:
            return False, self.ERRO_SEM_PERMISSAO
        
        adm = user_sess.user

        if user_sess.tipo != UserType.ESTACIONAMENTO:
            estacio = sess.query(Estacionamento).get(estacio_id)
        else:
            estacio = adm.estacionamento

        if estacio is None:
            return False, self.ERRO_ESTACIO_NAO_ENCONTRADO

        if estacio.cadastro_terminado is False:
            return False, self.ERRO_CADASTRO_NAO_FINALIZADO

        _val_nome = self._validate_nome(nome)
        if _val_nome:
            return False, _val_nome

        _val_total = self._validate_total_vaga(total_vaga)
        if _val_total:
            return False, _val_total
        
        _val_desc = self._validate_descricao(descricao)
        if _val_desc:
            return False, _val_desc

        _val_tel = self._validate_tel(telefone)
        if _val_tel:
            return False, _val_tel

        estacio.nome = nome or estacio.nome
        estacio.telefone = telefone or estacio.telefone
        estacio.total_vaga = total_vaga or estacio.total_vaga
        estacio.endereco = endereco or estacio.endereco

        if descricao is not None:
            descricao = descricao.strip()
            estacio.descricao = None if descricao == '' else descricao

        if foto is not None:
            try:
                fstream = self.image_processor.compress(foto, self.width_foto, self.height_foto)
            except AttributeError:
                return False, self.FOTO_FORMATO_INVALIDO
            except Exception as ex:
                logging.getLogger(__name__).error('edit(): Image processing error.', exc_info=ex)
                return False, self.FOTO_PROCESSING_ERRO

            try:
                fname = str(uuid4()) + '.' + self.image_processor.get_default_image_format()
                upload = self.uploader.upload(fstream, self.GROUP_UPLOAD_FOTO, fname)
            except Exception as ex:
                logging.getLogger(__name__).error('edit(): Upload error.', exc_info=ex)
                return False, self.ERRO_UPLOAD

            ori_id = int(estacio.foto_fk)
            self.uploader.delete(estacio.foto)

            estacio.foto = upload
            sess.query(Upload).filter(Upload.id == ori_id).delete()

        sess.commit()

        return True, estacio

    def list(self, sess: Session, amount: int = 0, index: int = 0) -> Tuple[bool, Union[str, Iterable[Estacionamento]]]:
        if index < 0:
            return True, tuple()

        query = sess.query(Estacionamento).offset(index)

        if amount > 0:
            query = query.limit(amount)

        estacios = query.all()

        return True, estacios

    def get(self, user_sess: UserSession, sess: Session, estacio_id: Optional[str] = None) -> Tuple[bool, Union[str, Estacionamento]]:
        if estacio_id is None:
            if user_sess is not None and user_sess.tipo == UserType.ESTACIONAMENTO:
                estacio = user_sess.user.estacionamento
            else:
                estacio = None
        else:
            estacio = sess.query(Estacionamento).get(estacio_id)
        
        if estacio is None:
            return False, self.ERRO_ESTACIO_NAO_ENCONTRADO

        return True, estacio

    def _validate_total_vaga(self, total_vaga: int) -> Optional[str]:
        if total_vaga is not None and total_vaga <= 0:
            return self.ERRO_TOTAL_VAGA_INV

    def _validate_descricao(self, descricao: Optional[str]) -> Optional[str]:
        if descricao is not None and len(descricao) > 2000:
            return self.ERRO_DESC_GRANDE

    def _validate_nome(self, nome: Optional[str]) -> Optional[str]:
        if nome is not None and len(nome) > 100:
            return self.ERRO_NOME_GRANDE

    def _validate_tel(self, tel: Optional[str]) -> Optional[str]:
        if tel is not None:
            if len(tel) > 20:
                return self.TEL_MUITO_GRANDE
            if not validate_telefone(tel):
                return self.TEL_FORMATO_INV
            if not tel.startswith('+') or len(tel) < 3:
                return self.TEL_SEM_COD_INTER
