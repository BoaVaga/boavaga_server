from sqlalchemy.orm import Session
from typing import Optional, Tuple, Union
import datetime

from src.classes import UserSession
from src.enums.user_type import UserType
from src.models import HorarioDivergente


class HorarioDivergenteRepo:
    ERRO_SEM_PERMISSAO = 'sem_permissao'
    ERRO_SEM_ESTACIO = 'sem_estacio'
    ERRO_FECHA_ANTES_ABRIR = 'fecha_antes_de_abrir'
    ERRO_DATA_PASSADA = 'data_passada'
    ERRO_DATA_NAO_ENCONTRADA = 'data_nao_encontrada'

    def set(self, user_sess: UserSession, sess: Session, data: datetime.date,
            hora_abre: datetime.time, hora_fecha: datetime.time) -> Tuple[bool, Union[str, HorarioDivergente]]:
        if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.ERRO_SEM_PERMISSAO

        estacio_fk = user_sess.user.estacio_fk
        if estacio_fk is None:
            return False, self.ERRO_SEM_ESTACIO

        if hora_fecha <= hora_abre:
            return False, self.ERRO_FECHA_ANTES_ABRIR

        if data < datetime.date.today():
            return False, self.ERRO_DATA_PASSADA

        horad = sess.query(HorarioDivergente).filter(
            (HorarioDivergente.estacio_fk==estacio_fk) & (HorarioDivergente.data == data)
        ).first()

        if horad is None:
            horad = HorarioDivergente(data=data, hora_abr=hora_abre, hora_fec=hora_fecha, estacio_fk=estacio_fk)
            sess.add(horad)
        else:
            horad.hora_abr, horad.hora_fec = hora_abre, hora_fecha

        sess.commit()

        return True, horad
    
    def delete(self, user_sess: UserSession, sess: Session, data: datetime.date) -> Tuple[bool, Optional[str]]:
        if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.ERRO_SEM_PERMISSAO

        estacio_fk = user_sess.user.estacio_fk
        if estacio_fk is None:
            return False, self.ERRO_SEM_ESTACIO

        count = sess.query(HorarioDivergente).filter(
            (HorarioDivergente.estacio_fk == estacio_fk) & (HorarioDivergente.data == data)
        ).delete()

        if count == 0:
            return False, self.ERRO_DATA_NAO_ENCONTRADA

        sess.commit()
        return True, None
