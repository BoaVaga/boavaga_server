from typing import Optional, Iterable, Tuple, Union

from sqlalchemy.orm import Session

from src.classes import UserSession, ValorHoraInput
from src.enums import UserType
from src.exceptions import ValidationError
from src.models import HorarioPadrao, Estacionamento


class EstacionamentoCrudRepo:
    ERRO_TOTAL_VAGA_INV = 'total_vaga_nao_positivo'
    ERRO_HORA_P_INV = 'hora_padrao_fecha_depois_de_abrir'
    ERRO_DESC_GRANDE = 'descricao_muito_grande'
    ERRO_VALOR_HORA_NAO_POSITIVO = 'valor_hora_preco_nao_positivo'
    ERRO_VALOR_HORA_VEICULO_NAO_ENCONTRADO = 'valor_hora_veiculo_nao_encontrado'
    ERRO_SEM_PERMISSAO = 'sem_permissao'
    ERRO_CADASTRO_FINALIZADO = 'cadastro_ja_terminado'

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

        if estacio.cadastro_terminado:
            return False, self.ERRO_CADASTRO_FINALIZADO

        if descricao is not None and len(descricao) > 2000:
            return False, self.ERRO_DESC_GRANDE
        if total_vaga <= 0:
            return False, self.ERRO_TOTAL_VAGA_INV

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
