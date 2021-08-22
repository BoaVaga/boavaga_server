from sqlalchemy import Column, SmallInteger, String

from src.models.base import Base


class Veiculo(Base):
    __tablename__ = 'veiculo'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    nome = Column(String(20), nullable=False)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Veiculo):
            return NotImplemented

        return (self.id == other.id and
                self.nome == other.nome)
