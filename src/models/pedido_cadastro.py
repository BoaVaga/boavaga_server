from sqlalchemy import Column, SmallInteger, String, ForeignKey
from sqlalchemy.orm import relationship

from src.models.admin_estacio import AdminEstacio
from src.models.endereco import Endereco
from src.models.base import Base


class PedidoCadastro(Base):
    __tablename__ = 'pedido_cadastro'

    id = Column(SmallInteger(), primary_key=True, nullable=False, autoincrement=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20), nullable=False)
    endereco_fk = Column(SmallInteger(), ForeignKey('endereco.id'), nullable=False)
    foto_fk = Column(SmallInteger(), ForeignKey('upload.id'), nullable=False)
    admin_estacio_fk = Column(SmallInteger(), ForeignKey('admin_estacio.id'), nullable=False)

    endereco = relationship('Endereco')
    foto = relationship('Upload')
    admin_estacio = relationship('AdminEstacio')

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, PedidoCadastro):
            return NotImplemented

        return (self.id == other.id and
                self.nome == other.nome and
                self.telefone == other.telefone and
                self.endereco_fk == other.endereco_fk and
                self.foto_fk == other.foto_fk and
                self.admin_estacio_fk == other.admin_estacio_fk)
