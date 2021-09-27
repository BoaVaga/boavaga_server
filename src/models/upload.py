from sqlalchemy import Column, SmallInteger, String, Enum

from src.enums import UploadStatus
from src.models.base import Base


class Upload(Base):
    __tablename__ = 'upload'

    id = Column(SmallInteger(), primary_key=True, autoincrement=True, nullable=False)
    nome_arquivo = Column(String(100), nullable=False)
    sub_dir = Column(String(100), nullable=False)
    status = Column(Enum(UploadStatus), nullable=False)

    def __hash__(self):
        return hash((self.id, self.nome_arquivo, self.sub_dir, self.status))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Upload):
            return NotImplemented

        return (self.id == other.id and
                self.nome_arquivo == other.nome_arquivo and
                self.sub_dir == other.sub_dir and
                self.status == other.status)

    def __repr__(self):
        return f'{self.sub_dir}/{self.nome_arquivo}'
