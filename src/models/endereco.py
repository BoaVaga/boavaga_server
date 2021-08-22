from sqlalchemy import Column, SmallInteger, String, Enum

from src.enums.estados_enum import EstadosEnum
from src.models.base import Base


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
