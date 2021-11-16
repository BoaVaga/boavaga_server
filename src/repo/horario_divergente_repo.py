from sqlalchemy.orm import Session
from typing import Optional, Tuple, Union
import datetime

from src.classes import UserSession
from src.models import HorarioDivergente


class HorarioDivergenteRepo:
    def set(self, user_sess: UserSession, sess: Session, data: datetime.date,
            hora_abre: datetime.time, hora_fecha: datetime.time) -> Tuple[bool, Union[str, HorarioDivergente]]:
        pass

    def delete(self, user_sess: UserSession, sess: Session, data: datetime.date) -> Tuple[bool, Optional[str]]:
        pass
