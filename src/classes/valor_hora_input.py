from decimal import Decimal

from sqlalchemy.orm import Session

from src.exceptions import ValidationError
from src.models import ValorHora, Veiculo


class ValorHoraInput:
    def __init__(self, veiculo_id: str, valor: Decimal):
        self.veiculo_id = veiculo_id
        self.valor = valor

    @staticmethod
    def from_dict(dct: dict):
        return ValorHoraInput(dct.get('veiculo_id'), Decimal(dct['valor']) if 'valor' in dct else None)

    def to_valor_hora(self, sess: Session) -> ValorHora:
        if self.valor <= 0:
            raise ValidationError('valor', 'Valor is not positive')

        veiculo = sess.query(Veiculo).get(self.veiculo_id)
        if veiculo is None:
            raise ValidationError('veiculo', 'Veiculo not found')

        return ValorHora(valor=self.valor, veiculo=veiculo)
