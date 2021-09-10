from sqlalchemy import Column, SmallInteger, String, LargeBinary

from src.models.base import Base


class AdminSistema(Base):  # IUser
    __tablename__ = 'admin_sistema'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    senha = Column(LargeBinary(60), nullable=False)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, AdminSistema):
            return NotImplemented

        return (self.id == other.id and
                self.email == other.email and
                self.senha == other.senha and
                self.nome == other.nome)
