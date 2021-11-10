from datetime import time
from decimal import Decimal
from typing import Tuple, Optional, Union

from sqlalchemy.orm import Session

from src.classes import UserSession
from src.enums import UserType
from src.models import HorarioPadrao, ValorHora
from src.models import estacionamento
from src.models.estacionamento import Estacionamento
from src.models.veiculo import Veiculo
from src.utils.db_utils import db_check_if_exists

_DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')


class EstacionamentoOthersRepo:
    ERRO_QTD_NEGATIVA = 'quantia_negativa'
    ERRO_QTD_MAIOR_Q_TOTAL = 'quantia_maior_que_total'
    ERRO_SEM_ESTACIO = 'sem_estacionamento'
    ERRO_SEM_PERMISSAO = 'sem_permissao'
    ERRO_ESTACIO_NAO_ENCONTRADO = 'estacio_nao_encontrado'
    ERRO_VEICULO_NAO_ENCONTRADO = 'veiculo_nao_encontrado'
    ERRO_VALOR_NAO_POSITIVO = 'valor_nao_positivo'
    ERRO_VALOR_HORA_NAO_ENCONTRADO = 'valor_hora_nao_encontrado'
    ERRO_DIA_INVALIDO = 'dia_invalido'
    ERRO_FECHA_ANTES_DE_ABRIR = 'hora_padrao_fecha_antes_de_abrir'

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
        if user_sess is None:
            return False, self.ERRO_SEM_PERMISSAO

        if hora_fecha <= hora_abre:
            return False, self.ERRO_FECHA_ANTES_DE_ABRIR

        if user_sess.tipo == UserType.ESTACIONAMENTO:
            estacio = user_sess.user.estacionamento
        else:
            estacio = sess.query(Estacionamento).get(estacio_id)

        horap = estacio.horario_padrao
        dia = dia.strip().lower()
        if dia not in _DIAS:
            return False, self.ERRO_DIA_INVALIDO

        setattr(horap, '_'.join((dia, 'abr')), hora_abre)
        setattr(horap, '_'.join((dia, 'fec')), hora_fecha)

        sess.commit()

        return True, horap

    def edit_valor_hora(self, user_sess: UserSession, sess: Session, veiculo_id: str, valor: Decimal,
                        estacio_id: Optional[str] = None) -> Tuple[bool, Union[str, ValorHora]]:
        if user_sess is None:
            return False, self.ERRO_SEM_PERMISSAO
        elif user_sess.tipo == UserType.ESTACIONAMENTO:
            estacio_id = user_sess.user.estacio_fk

        if valor <= 0:
            return False, self.ERRO_VALOR_NAO_POSITIVO

        valor_hora = sess.query(ValorHora).filter(
            (ValorHora.estacio_fk == estacio_id) & (ValorHora.veiculo_fk == veiculo_id)
        ).first()

        if valor_hora is None:
            veiculo = sess.query(Veiculo).get(veiculo_id)
            if veiculo is None:
                return False, self.ERRO_VEICULO_NAO_ENCONTRADO
            if db_check_if_exists(sess, Estacionamento, estacio_id) is not True:
                return False, self.ERRO_ESTACIO_NAO_ENCONTRADO

            valor_hora = ValorHora(veiculo=veiculo, valor=valor, estacio_fk=estacio_id)
        else:
            valor_hora.valor = valor

        sess.commit()

        return True, valor_hora

    def delete_valor_hora(self, user_sess: UserSession, sess: Session, veiculo_id: str,
                          estacio_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        if user_sess is None:
            return False, self.ERRO_SEM_PERMISSAO

        estacio_id = estacio_id or user_sess.user.estacio_fk

        count = sess.query(ValorHora).filter(
            (ValorHora.estacio_fk == estacio_id) & (ValorHora.veiculo_fk == veiculo_id)
        ).delete()

        if count == 0:
            return False, self.ERRO_VALOR_HORA_NAO_ENCONTRADO

        sess.commit()

        return True, None
