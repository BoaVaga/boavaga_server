from typing import Optional

from sqlalchemy import Column, SmallInteger, Time
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.utils import time_from_total_seconds

_DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')


class HorarioPadrao(Base):
    __tablename__ = 'horario_padrao'

    id = Column(SmallInteger, primary_key=True, autoincrement=True, nullable=False)
    segunda_abr = Column(Time(), nullable=True)
    segunda_fec = Column(Time(), nullable=True)
    terca_abr = Column(Time(), nullable=True)
    terca_fec = Column(Time(), nullable=True)
    quarta_abr = Column(Time(), nullable=True)
    quarta_fec = Column(Time(), nullable=True)
    quinta_abr = Column(Time(), nullable=True)
    quinta_fec = Column(Time(), nullable=True)
    sexta_abr = Column(Time(), nullable=True)
    sexta_fec = Column(Time(), nullable=True)
    sabado_abr = Column(Time(), nullable=True)
    sabado_fec = Column(Time(), nullable=True)
    domingo_abr = Column(Time(), nullable=True)
    domingo_fec = Column(Time(), nullable=True)

    estacionamento = relationship('Estacionamento', back_populates='horario_padrao', uselist=False)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, HorarioPadrao):
            return NotImplemented

        return (self.id == other.id and
                self.segunda_abr == other.segunda_abr and
                self.terca_abr == other.terca_abr and
                self.quarta_abr == other.quarta_abr and
                self.quinta_abr == other.quinta_abr and
                self.sexta_abr == other.sexta_abr and
                self.sabado_abr == other.sabado_abr and
                self.domingo_abr == other.domingo_abr and
                self.segunda_fec == other.segunda_fec and
                self.terca_fec == other.terca_fec and
                self.quarta_fec == other.quarta_fec and
                self.quinta_fec == other.quinta_fec and
                self.sexta_fec == other.sexta_fec and
                self.sabado_fec == other.sabado_fec and
                self.domingo_fec == other.domingo_fec)

    @staticmethod
    def from_dict(dct: dict):
        _id = int(dct['id']) if 'id' in dct is not None else None
        _kwargs = {'id': _id}

        for dia in _DIAS:
            for tipo in ['abr', 'fec']:
                k = '_'.join((dia, tipo))
                _kwargs[k] = time_from_total_seconds(int(dct[k])) if k in dct else None

        return HorarioPadrao(**_kwargs)

    def validate(self) -> Optional[str]:
        for dia in _DIAS:
            abr, fec = getattr(self, '_'.join((dia, 'abr'))), getattr(self, '_'.join((dia, 'fec')))

            if abr is not None and fec is not None:
                if fec <= abr:
                    return 'hora_padrao_fecha_antes_de_abrir'
            elif abr is not None or fec is not None:
                return 'hora_padrao_dia_incompleto'
