from typing import Tuple, Union, Iterable

from sqlalchemy.orm import Session

from src.models import Veiculo


class VeiculoCrudRepo:
    ERRO_VEICULO_NAO_ENCONTRADO = 'veiculo_nao_encontrado'

    def list(self, sess: Session) -> Tuple[bool, Union[str, Iterable[Veiculo]]]:
        return True, sess.query(Veiculo).all()

    def get(self, sess: Session, veiculo_id: str) -> Tuple[bool, Union[str, Veiculo]]:
        veiculo = sess.query(Veiculo).get(veiculo_id)
        if veiculo is None:
            return False, self.ERRO_VEICULO_NAO_ENCONTRADO

        return True, veiculo
