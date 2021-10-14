from sqlalchemy import Column, SmallInteger, String, LargeBinary, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from src.models.base import Base


class AdminEstacio(Base):  # IUser
    __tablename__ = 'admin_estacio'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False, unique=True)
    senha = Column(LargeBinary(60), nullable=False)
    admin_mestre = Column(Boolean(), nullable=False, default=False)
    estacio_fk = Column(SmallInteger(), ForeignKey('estacionamento.id'), nullable=True)

    estacionamento = relationship('Estacionamento')

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, AdminEstacio):
            return NotImplemented

        return (self.id == other.id and
                self.email == other.email and
                self.senha == other.senha and
                self.admin_mestre == other.admin_mestre and
                self.estacio_fk == other.estacio_fk)
