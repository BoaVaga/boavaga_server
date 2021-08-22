from sqlalchemy import Column, SmallInteger, Date, Time, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import Base


class HorarioDivergente(Base):
    __tablename__ = 'horario_divergente'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    data = Column(Date(), nullable=False)
    hora_abr = Column(Time(), nullable=False)
    hora_fec = Column(Time(), nullable=False)
    estacio_fk = Column(SmallInteger(), ForeignKey('estacionamento.id'), nullable=False)

    estacionamento = relationship('Estacionamento', back_populates='horas_divergentes')

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, HorarioDivergente):
            return NotImplemented

        return (self.id == other.id and
                self.data == other.data and
                self.hora_abr == other.hora_abr and
                self.hora_fec == other.hora_fec and
                self.estacio_fk == other.estacio_fk)
