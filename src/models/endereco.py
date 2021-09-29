from typing import Optional

from sqlalchemy import Column, SmallInteger, String, Enum

from src.enums import EstadosEnum
from src.models.base import Base

MAX_LEN_ATTRS = {
    'logradouro': 100, 'cidade': 50, 'bairro': 50, 'numero': 10
}


class Endereco(Base):
    __tablename__ = 'endereco'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    logradouro = Column(String(100), nullable=False)
    estado = Column(Enum(EstadosEnum), nullable=False)
    cidade = Column(String(50), nullable=False)
    bairro = Column(String(50), nullable=False)
    numero = Column(String(10), nullable=True)
    cep = Column(String(8), nullable=False)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Endereco):
            return NotImplemented

        return (self.id == other.id and
                self.logradouro == other.logradouro and
                self.estado == other.estado and
                self.cidade == other.cidade and
                self.bairro == other.bairro and
                self.numero == other.numero and
                self.cep == other.cep)

    def to_dict(self):
        return {
            'id': self.id, 'logradouro': self.logradouro, 'estado': self.estado.name, 'cidade': self.cidade,
            'bairro': self.bairro, 'numero': self.numero, 'cep': self.cep
        }

    @staticmethod
    def from_dict(dct: dict):
        _id = int(dct.get('id')) if dct.get('id') is not None else None
        _est = dct.get('estado')
        if _est is None or not isinstance(_est, EstadosEnum):
            _est = EstadosEnum[dct.get('estado')]

        return Endereco(id=_id, logradouro=dct.get('logradouro'), estado=_est, cidade=dct.get('cidade'),
                        bairro=dct.get('bairro'), numero=dct.get('numero'), cep=dct.get('cep'))

    def validate(self) -> Optional[str]:
        nome_check_empty = ('logradouro', 'estado', 'cidade', 'bairro', 'numero', 'cep')
        for nome in nome_check_empty:
            if not getattr(self, nome):
                return f'end_{nome}_vazio'

        for nome, max_len in MAX_LEN_ATTRS.items():
            if len(getattr(self, nome)) > max_len:
                return f'end_{nome}_muito_grande'

        if not self.cep.isdecimal() or len(self.cep) > 8:
            return 'end_cep_invalido'
