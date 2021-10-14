from decimal import Decimal

from sqlalchemy import Column, SmallInteger, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from src.models.veiculo import Veiculo
from src.models.base import Base


class ValorHora(Base):
    __tablename__ = 'valor_hora'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    valor = Column(Numeric(4, 2), nullable=False)
    veiculo_fk = Column(SmallInteger(), ForeignKey('veiculo.id'), nullable=False)
    estacio_fk = Column(SmallInteger(), ForeignKey('estacionamento.id'), nullable=False)

    veiculo = relationship('Veiculo')
    estacionamento = relationship('Estacionamento', back_populates='valores_hora')

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, ValorHora):
            return NotImplemented

        return (self.id == other.id and
                self.valor == other.valor and
                self.veiculo_fk == other.veiculo_fk and
                self.estacio_fk == other.estacio_fk)

    @staticmethod
    def from_dict(dct: dict):
        _id = int(dct['id']) if 'id' in dct is not None else None
        valor = Decimal(dct['valor']) if 'valor' in dct else None
        veiculo = Veiculo(nome=dct['veiculo']) if 'veiculo' in dct is not None else None

        return ValorHora(id=_id, valor=valor, veiculo=veiculo)
