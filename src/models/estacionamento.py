from sqlalchemy import Column, SmallInteger, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import Base


class Estacionamento(Base):
    __tablename__ = 'estacionamento'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    nome = Column(String(100), nullable=False)
    esta_suspenso = Column(Boolean(), nullable=False)
    esta_aberto = Column(Boolean(), nullable=False)
    descricao = Column(Text(), nullable=True)
    telefone = Column(String(20), nullable=False)
    qtd_vaga_livre = Column(SmallInteger(), nullable=False)
    horap_fk = Column(SmallInteger(), ForeignKey('horario_padrao.id'), nullable=False)
    endereco_fk = Column(SmallInteger(), ForeignKey('endereco.id'), nullable=False)
    foto_fk = Column(SmallInteger(), ForeignKey('upload.id'), nullable=False)

    horario_padrao = relationship('HorarioPadrao', back_populates='estacionamento')
    endereco = relationship('Endereco')
    foto = relationship('Upload')
    valores_hora = relationship('ValorHora', back_populates='estacionamento')
    horas_divergentes = relationship('HorarioDivergente', back_populates='estacionamento')

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Estacionamento):
            return NotImplemented

        return (self.id == other.id and
                self.nome == other.nome and
                self.esta_suspenso == other.esta_suspenso and
                self.esta_aberto == other.esta_aberto and
                self.descricao == other.descricao and
                self.telefone == other.telefone and
                self.qtd_vaga_livre == other.qtd_vaga_livre and
                self.horap_fk == other.horap_fk and
                self.endereco_fk == other.endereco_fk and
                self.foto_fk == other.foto_fk)
