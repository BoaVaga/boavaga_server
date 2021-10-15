from decimal import Decimal

from sqlalchemy.orm import Session

from src.models import ValorHora, Veiculo


class ValorHoraInput:
    def __init__(self, veiculo_id: str, valor: Decimal):
        self.veiculo_id = veiculo_id
        self.valor = valor

    @staticmethod
    def from_dict(dct: dict):
        return ValorHoraInput(dct.get('veiculo_id'), Decimal(dct['valor']) if 'valor' in Decimal else None)

    def to_valor_hora(self, sess: Session) -> ValorHora:
        veiculo = sess.query(Veiculo).get(self.veiculo_id)
        return ValorHora(valor=self.valor, veiculo=veiculo)
