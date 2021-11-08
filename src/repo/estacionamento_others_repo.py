from datetime import time
from decimal import Decimal
from typing import Tuple, Optional, Union

from sqlalchemy.orm import Session

from src.classes import UserSession
from src.enums import UserType
from src.models import HorarioPadrao, ValorHora


class EstacionamentoOthersRepo:
    ERRO_QTD_NEGATIVA = 'quantia_negativa'
    ERRO_QTD_MAIOR_Q_TOTAL = 'quantia_maior_que_total'
    ERRO_SEM_ESTACIO = 'sem_estacionamento'
    ERRO_SEM_PERMISSAO = 'sem_permissao'

    def atualizar_vagas_livres(self, user_sess: UserSession, sess: Session, num_vagas: int) \
            -> Tuple[bool, Optional[str]]:
        if user_sess is None:
            return False, self.ERRO_SEM_PERMISSAO

        if num_vagas < 0:
            return False, self.ERRO_QTD_NEGATIVA
        if user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.ERRO_SEM_ESTACIO

        estacio = user_sess.user.estacionamento
        if estacio is None:
            return False, self.ERRO_SEM_ESTACIO

        if num_vagas > estacio.total_vaga:
            return False, self.ERRO_QTD_MAIOR_Q_TOTAL

        estacio.qtd_vaga_livre = num_vagas

        sess.commit()
        return True, None

    def edit_horario_padrao(self, user_sess: UserSession, sess: Session, dia: str, hora_abre: time, hora_fecha: time,
                            estacio_id: Optional[str] = None) -> Tuple[bool, Union[str, HorarioPadrao]]:
        pass

    def edit_valor_hora(self, user_sess: UserSession, sess: Session, veiculo_id: str, valor: Decimal,
                        estacio_id: Optional[str] = None) -> Tuple[bool, Union[str, ValorHora]]:
        pass
