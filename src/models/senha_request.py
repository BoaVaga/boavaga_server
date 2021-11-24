from sqlalchemy import Column, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime, String

from src.models.base import Base


class SenhaRequest(Base):
    __tablename__ = 'senha_request'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    code = Column(String(8), nullable=False, unique=True)
    admin_estacio_fk = Column(SmallInteger(), ForeignKey('admin_estacio.id'), nullable=True, unique=True)
    admin_sistema_fk = Column(SmallInteger(), ForeignKey('admin_sistema.id'), nullable=True, unique=True)
    data_criacao = Column(DateTime(), nullable=False)

    admin_estacio = relationship('AdminEstacio')
    admin_sistema = relationship('AdminSistema')


    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, SenhaRequest):
            return NotImplemented

        return (self.id == other.id and
                self.code == other.code and
                self.admin_estacio_fk == other.admin_estacio_fk and
                self.admin_sistema_fk == other.admin_sistema_fk and
                self.data_criacao == other.data_criacao)
