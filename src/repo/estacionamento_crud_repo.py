from typing import Optional, Iterable, Tuple, Union

from sqlalchemy.orm import Session

from src.classes import UserSession, ValorHoraInput
from src.models import HorarioPadrao, Estacionamento, AdminEstacio, ValorHora


class EstacionamentoCrudRepo:
    def create(
        self, user_sess: UserSession, sess: Session,
        total_vaga: int,
        horario_padrao: HorarioPadrao,
        valores_hora: Optional[Iterable[ValorHoraInput]] = None,
        estacio_id: Optional[str] = None,
        descricao: Optional[str] = None
    ) -> Tuple[bool, Union[str, Estacionamento]]:
        adm: AdminEstacio = user_sess.user
        estacio: Estacionamento = adm.estacionamento

        real_valores_hora = [v.to_valor_hora(sess) for v in valores_hora]

        estacio.total_vaga = estacio.qtd_vaga_livre = total_vaga
        estacio.descricao = descricao
        estacio.horario_padrao = horario_padrao
        estacio.valores_hora = real_valores_hora

        sess.commit()

        return True, estacio
